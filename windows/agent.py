import os
import json
import time
import subprocess
import platform
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

import requests

DEFAULT_INTERVAL = 5
AGENT_VERSION = "1.3"  # Incrementar a cada atualização


def load_agent_config() -> Dict[str, Any]:
    cfg_path = Path(__file__).parent / "agent.json"
    cfg: Dict[str, Any] = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    # Env overrides
    server = os.getenv("AGENT_SERVER", cfg.get("server", "http://localhost:9000"))
    token = os.getenv("AGENT_TOKEN", cfg.get("token"))
    interval_sec = int(os.getenv("AGENT_INTERVAL_SEC", str(cfg.get("interval_sec", DEFAULT_INTERVAL))))
    loop = os.getenv("AGENT_LOOP", str(cfg.get("loop", "false"))).lower() in ("1", "true", "yes")
    cameras = cfg.get("cameras") if isinstance(cfg.get("cameras"), list) else []
    # Speedtest options (optional)
    speed_enabled = os.getenv("AGENT_SPEEDTEST", str(cfg.get("speedtest", "1"))).lower() in ("1", "true", "yes")
    try:
        speed_dl = int(os.getenv("AGENT_SPEEDTEST_DOWNLOAD_BYTES", str(cfg.get("speed_download_bytes", 1024 * 1024))))
    except Exception:
        speed_dl = 1024 * 1024
    try:
        speed_ul = int(os.getenv("AGENT_SPEEDTEST_UPLOAD_BYTES", str(cfg.get("speed_upload_bytes", 512 * 1024))))
    except Exception:
        speed_ul = 512 * 1024
    return {
        "server": server.rstrip("/"),
        "token": token,
        "interval_sec": interval_sec,
        "loop": loop,
        "cameras": cameras,
        "speedtest": speed_enabled,
        "speed_download_bytes": speed_dl,
        "speed_upload_bytes": speed_ul,
    }


def ping_ip(ip: str, count: int = 4, timeout_ms: int = 1000, retry: int = 2) -> Tuple[bool, Optional[float], Optional[float], str]:
    """
    Retorna: (reachable, avg_latency_ms, packet_loss_percent, raw_output_tail)
    
    Melhorias:
    - Retry automático em caso de falha (reduz falsos negativos)
    - Validação de latência suspeita (detecta falsos positivos)
    - Melhor parsing de output em diferentes idiomas
    """
    import re as _re
    
    is_windows = platform.system().lower().startswith("win")
    if is_windows:
        cmd = ["ping", "-n", str(count), "-w", str(timeout_ms), ip]
    else:
        # -W 1 (segundos no Linux), -c count
        cmd = ["ping", "-c", str(count), "-W", "1", ip]
    
    last_error = None
    
    # Tentar até 'retry' vezes para reduzir falsos negativos
    for attempt in range(retry):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max(3, count * 2))
            output = (proc.stdout or "") + (proc.stderr or "")
            reachable = proc.returncode == 0
            avg_ms: Optional[float] = None
            loss_pct: Optional[float] = None
            
            if is_windows:
                # Ex.: Média = 4ms ou Average = 4ms
                for line in output.splitlines():
                    line = line.strip()
                    # Suporta PT e EN
                    if "média" in line.lower() or "average" in line.lower():
                        # Pegar número antes de 'ms'
                        m = _re.search(r"(\d+)\s*ms", line, _re.IGNORECASE)
                        if m:
                            avg_ms = float(m.group(1))
                
                # Perda: "Perdidos = X (Y% perda)" ou "Lost = X (Y% loss)"
                for line in output.splitlines():
                    if "perdidos" in line.lower() or "lost" in line.lower():
                        m = _re.search(r"\((\d+)\s*%", line)
                        if m:
                            loss_pct = float(m.group(1))
            else:
                # Linux/mac output: rtt min/avg/max/mdev = 0.345/0.456/...
                for line in output.splitlines():
                    if "rtt min/avg/max" in line or "round-trip min/avg/max" in line:
                        try:
                            part = line.split("=")[-1].strip().split("/")
                            avg_ms = float(part[1])
                        except Exception:
                            pass
                
                for line in output.splitlines():
                    if "% packet loss" in line:
                        try:
                            loss_pct = float(line.split("% packet loss")[0].split(" ")[-1])
                        except Exception:
                            pass
            
            # Validação: detectar falsos positivos
            # Se returncode = 0 mas perda = 100%, considerar offline
            if reachable and loss_pct is not None and loss_pct >= 100.0:
                reachable = False
            
            # Se returncode = 0 mas não conseguiu extrair latência, pode ser falso positivo
            # Verificar se há pelo menos uma resposta bem-sucedida no output
            if reachable and avg_ms is None:
                # Procurar por padrões de resposta bem-sucedida
                success_patterns = [
                    r"bytes?\s+from",  # Linux: "bytes from"
                    r"resposta\s+de",  # Windows PT: "Resposta de"
                    r"reply\s+from",   # Windows EN: "Reply from"
                    r"ttl\s*=",        # TTL presente indica resposta
                ]
                has_success = any(_re.search(pattern, output, _re.IGNORECASE) for pattern in success_patterns)
                if not has_success:
                    reachable = False
            
            # Se bem-sucedido, retornar imediatamente
            if reachable:
                return reachable, avg_ms, loss_pct, output[-500:]
            
            # Se falhou mas ainda há tentativas, continuar
            last_error = output[-500:]
            
            # Pequeno delay antes de retry (100ms)
            if attempt < retry - 1:
                time.sleep(0.1)
                
        except Exception as e:
            last_error = f"ping error: {e}"
            if attempt < retry - 1:
                time.sleep(0.1)
            continue
    
    # Todas as tentativas falharam
    return False, None, None, last_error or "ping failed after retries"


def get_mac_address(ip: str) -> Optional[str]:
    """
    Obtém o MAC address de um IP usando tabela ARP.
    Retorna MAC no formato AA:BB:CC:DD:EE:FF ou None se não encontrado.
    """
    import re as _re
    
    is_windows = platform.system().lower().startswith("win")
    
    try:
        # Primeiro, fazer ping para popular tabela ARP
        ping_ip(ip, count=1, timeout_ms=500, retry=1)
        
        if is_windows:
            # Windows: arp -a IP
            proc = subprocess.run(["arp", "-a", ip], capture_output=True, text=True, timeout=5)
        else:
            # Linux/Mac: arp -n IP ou ip neigh show IP
            proc = subprocess.run(["arp", "-n", ip], capture_output=True, text=True, timeout=5)
        
        output = proc.stdout + proc.stderr
        
        # Procurar padrão de MAC address (vários formatos)
        # AA:BB:CC:DD:EE:FF ou AA-BB-CC-DD-EE-FF ou AABBCCDDEEFF
        mac_patterns = [
            r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})",  # AA:BB:CC:DD:EE:FF ou AA-BB-CC-DD-EE-FF
            r"([0-9A-Fa-f]{12})",  # AABBCCDDEEFF
        ]
        
        for pattern in mac_patterns:
            match = _re.search(pattern, output)
            if match:
                mac = match.group(0)
                # Normalizar para formato AA:BB:CC:DD:EE:FF
                mac = mac.replace("-", ":")
                if len(mac) == 12:  # AABBCCDDEEFF
                    mac = ":".join([mac[i:i+2] for i in range(0, 12, 2)])
                return mac.upper()
        
        return None
        
    except Exception as e:
        print(f"[agent] get_mac_address error for {ip}: {e}")
        return None


def scan_network_for_mac(mac: str, network_prefix: str, timeout_sec: int = 30) -> Optional[str]:
    """
    Varre a rede procurando um dispositivo com o MAC address especificado.
    
    Args:
        mac: MAC address no formato AA:BB:CC:DD:EE:FF
        network_prefix: Prefixo da rede (ex: "192.168.1.")
        timeout_sec: Timeout total para o scan
    
    Returns:
        IP encontrado ou None
    """
    import concurrent.futures
    import re as _re
    
    mac_normalized = mac.upper().replace("-", ":")
    start_time = time.time()
    
    print(f"[agent] Scanning network {network_prefix}0/24 for MAC {mac_normalized}...")
    
    def check_ip(suffix: int) -> Optional[str]:
        """Verifica se um IP específico tem o MAC procurado"""
        if time.time() - start_time > timeout_sec:
            return None
        
        ip = f"{network_prefix}{suffix}"
        found_mac = get_mac_address(ip)
        
        if found_mac and found_mac.upper() == mac_normalized:
            print(f"[agent] Found MAC {mac_normalized} at {ip}")
            return ip
        
        return None
    
    # Scan paralelo para ser mais rápido (máx 20 threads)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Varrer IPs de 1 a 254
        futures = {executor.submit(check_ip, i): i for i in range(1, 255)}
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result:
                    # Cancelar outras tarefas
                    for f in futures:
                        f.cancel()
                    return result
            except Exception:
                pass
    
    print(f"[agent] MAC {mac_normalized} not found in network {network_prefix}0/24")
    return None


def test_network() -> Dict[str, Any]:
    net: Dict[str, Any] = {}
    reachable_1, avg1, _, _ = ping_ip("1.1.1.1", count=4)
    reachable_8, avg8, _, _ = ping_ip("8.8.8.8", count=4)
    net["ping_1_1_1_1_ms"] = avg1 if reachable_1 else None
    net["ping_8_8_8_8_ms"] = avg8 if reachable_8 else None
    # DNS
    try:
        socket.gethostbyname("google.com")
        net["dns_ok"] = True
    except Exception:
        net["dns_ok"] = False
    # HTTP
    try:
        requests.get("https://www.google.com", timeout=5)
        net["http_ok"] = True
    except Exception:
        net["http_ok"] = False
    return net


def bytes_to_mbps(byte_count: int, seconds: float) -> Optional[float]:
    try:
        if seconds <= 0:
            return None
        # Mbps = (bytes * 8) / (seconds * 1e6)
        mbps = (byte_count * 8) / (seconds * 1_000_000)
        # Arredondar para 2 casas decimais
        return round(mbps, 2)
    except Exception:
        return None


def internet_speedtest() -> Dict[str, Any]:
    """Runs an internet speedtest using the Ookla Speedtest CLI if available.
    Requires `speedtest` command in PATH.
    Returns keys prefixed with inet_*.
    """
    out: Dict[str, Any] = {
        "inet_download_mbps": None,
        "inet_upload_mbps": None,
        "inet_ping_ms": None,
        "inet_isp": None,
        "inet_server_name": None,
        "inet_error": None,
    }

    def _parse_first_json(raw: str) -> Optional[Dict[str, Any]]:
        raw = (raw or "").strip()
        if not raw:
            return None
        try:
            js = json.loads(raw)
            return js if isinstance(js, dict) else None
        except Exception:
            pass
        # fallback: find the first JSON object in mixed output
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                js = json.loads(raw[start : end + 1])
                return js if isinstance(js, dict) else None
        except Exception:
            pass
        return None
    def _from_ookla_json(js: Dict[str, Any]) -> Dict[str, Any]:
        # Ookla JSON: download.bandwidth (bytes/s), upload.bandwidth (bytes/s), ping.latency (ms)
        dl_bw = None
        ul_bw = None
        ping_ms = None
        try:
            dl_bw = js.get("download", {}).get("bandwidth")
            ul_bw = js.get("upload", {}).get("bandwidth")
            ping_ms = js.get("ping", {}).get("latency")
        except Exception:
            pass

        try:
            if isinstance(dl_bw, (int, float)):
                out["inet_download_mbps"] = round((float(dl_bw) * 8) / 1_000_000, 2)
        except Exception:
            pass
        try:
            if isinstance(ul_bw, (int, float)):
                out["inet_upload_mbps"] = round((float(ul_bw) * 8) / 1_000_000, 2)
        except Exception:
            pass
        try:
            if isinstance(ping_ms, (int, float)):
                out["inet_ping_ms"] = round(float(ping_ms), 2)
        except Exception:
            pass

        try:
            out["inet_isp"] = js.get("isp")
        except Exception:
            pass
        try:
            out["inet_server_name"] = js.get("server", {}).get("name")
        except Exception:
            pass
        return out

    def _from_speedtest_cli_json(js: Dict[str, Any]) -> Dict[str, Any]:
        # speedtest-cli (python) JSON: download (bits/s), upload (bits/s), ping (ms), client.isp, server.sponsor/name
        try:
            dl_bps = js.get("download")
            ul_bps = js.get("upload")
            ping_ms = js.get("ping")
            if isinstance(dl_bps, (int, float)):
                out["inet_download_mbps"] = round(float(dl_bps) / 1_000_000, 2)
            if isinstance(ul_bps, (int, float)):
                out["inet_upload_mbps"] = round(float(ul_bps) / 1_000_000, 2)
            if isinstance(ping_ms, (int, float)):
                out["inet_ping_ms"] = round(float(ping_ms), 2)
        except Exception:
            pass
        try:
            out["inet_isp"] = js.get("client", {}).get("isp")
        except Exception:
            pass
        try:
            srv = js.get("server", {})
            out["inet_server_name"] = srv.get("sponsor") or srv.get("name")
        except Exception:
            pass
        return out

    try:
        proc = subprocess.run(["speedtest-cli", "--json"], capture_output=True, text=True, timeout=180)
        if proc.returncode == 0:
            js = _parse_first_json((proc.stdout or "") + "\n" + (proc.stderr or ""))
            if isinstance(js, dict):
                out["inet_error"] = None
                return _from_speedtest_cli_json(js)
    except Exception:
        pass

    try:
        proc = subprocess.run(["speedtest", "--json"], capture_output=True, text=True, timeout=180)
        if proc.returncode == 0:
            js = _parse_first_json((proc.stdout or "") + "\n" + (proc.stderr or ""))
            if isinstance(js, dict):
                out["inet_error"] = None
                return _from_speedtest_cli_json(js)
    except Exception:
        pass

    try:
        proc = subprocess.run([sys.executable, "-m", "speedtest", "--json"], capture_output=True, text=True, timeout=180)
        if proc.returncode == 0:
            js = _parse_first_json((proc.stdout or "") + "\n" + (proc.stderr or ""))
            if isinstance(js, dict):
                out["inet_error"] = None
                return _from_speedtest_cli_json(js)
    except Exception:
        pass

    try:
        # Só tente a CLI Ookla se ela estiver realmente instalada.
        try:
            v = subprocess.run(["speedtest", "--version"], capture_output=True, text=True, timeout=10)
            v_raw = ((v.stdout or "") + "\n" + (v.stderr or "")).lower()
            if "ookla" not in v_raw:
                raise FileNotFoundError("speedtest command is not ookla")
        except FileNotFoundError:
            raise
        except Exception:
            # Se não der para identificar, não arrisque rodar com flags específicas.
            raise FileNotFoundError("speedtest command is not ookla")

        cmd = ["speedtest", "--accept-license", "--accept-gdpr", "--format=json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        raw = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            lower = raw.lower()
            if "unrecognized arguments" in lower or "error: unrecognized arguments" in lower:
                raise FileNotFoundError("speedtest command is not ookla")
            out["inet_error"] = raw[-400:] or f"speedtest exit {proc.returncode}"
            return out
        js = _parse_first_json(proc.stdout or "")
        if isinstance(js, dict):
            out["inet_error"] = None
            return _from_ookla_json(js)
        out["inet_error"] = "invalid_json_structure"
        return out
    except FileNotFoundError:
        pass
    except Exception as e:
        out["inet_error"] = str(e)
        return out

    try:
        import speedtest as _speedtest  # type: ignore

        if not hasattr(_speedtest, "Speedtest"):
            out["inet_error"] = "python_package_conflict: pacote 'speedtest' incorreto. Execute: python -m pip uninstall -y speedtest && python -m pip install speedtest-cli"
            return out

        st = _speedtest.Speedtest()
        st.get_best_server()
        dl_bps = st.download()
        ul_bps = st.upload()
        try:
            res = st.results.dict()
        except Exception:
            res = {}

        js: Dict[str, Any] = {
            "download": dl_bps,
            "upload": ul_bps,
            "ping": res.get("ping"),
            "client": {"isp": (res.get("client") or {}).get("isp") if isinstance(res.get("client"), dict) else None},
            "server": {
                "sponsor": (res.get("server") or {}).get("sponsor") if isinstance(res.get("server"), dict) else None,
                "name": (res.get("server") or {}).get("name") if isinstance(res.get("server"), dict) else None,
            },
        }
        out["inet_error"] = None
        return _from_speedtest_cli_json(js)
    except Exception as e:
        out["inet_error"] = str(e)
        return out



def speedtest(server: str, download_bytes: int, upload_bytes: int, token: Optional[str]) -> Dict[str, Any]:
    """Measure download/upload throughput using API endpoints provided by the server.
    Returns: { download_mbps, upload_mbps }
    """
    out: Dict[str, Any] = {
        "download_mbps": None,
        "upload_mbps": None,
        "download_error": None,
        "upload_error": None,
        "download_seconds": None,
        "upload_seconds": None,
        "download_bytes": int(download_bytes),
        "upload_bytes": int(upload_bytes),
    }
    headers = {"X-Agent-Token": token} if token else {}

    # Download test - com melhorias de precisão
    try:
        url_dl = f"{server}/api/speedtest/download?size_bytes={max(1, int(download_bytes))}"
        r = requests.get(url_dl, headers=headers, stream=True, timeout=30)
        r.raise_for_status()
        
        total = 0
        chunk_count = 0
        warmup_chunks = 2  # Descartar primeiros chunks (conexão inicial)
        t0 = None
        
        # Usar chunks maiores para reduzir overhead de processamento
        for chunk in r.iter_content(chunk_size=256 * 1024):
            if not chunk:
                continue
            
            chunk_count += 1
            
            # Iniciar timer após warm-up
            if chunk_count == warmup_chunks + 1:
                t0 = time.perf_counter()  # Mais preciso que monotonic
            
            # Contar apenas após warm-up
            if chunk_count > warmup_chunks:
                total += len(chunk)
        
        if t0 is not None and total > 0:
            dt = time.perf_counter() - t0
            out["download_mbps"] = bytes_to_mbps(total, dt)
            out["download_seconds"] = round(dt, 3)
            out["download_bytes"] = total
        else:
            out["download_error"] = "Insufficient data received"
    except Exception as e:
        out["download_error"] = str(e)
        print(f"[agent] speedtest download error: {e}")

    # Upload test - com melhorias de precisão
    try:
        url_ul = f"{server}/api/speedtest/upload"
        payload = b"\x00" * max(1, int(upload_bytes))
        
        # Medir tempo de upload mais precisamente
        t0 = time.perf_counter()
        r = requests.post(url_ul, headers=headers, data=payload, timeout=30)
        dt = time.perf_counter() - t0
        
        r.raise_for_status()
        
        # Preferir bytes confirmados pelo servidor
        acknowledged = None
        try:
            js = r.json()
            acknowledged = int(js.get("received_bytes")) if isinstance(js, dict) else None
        except Exception:
            acknowledged = None
        
        sent = acknowledged if acknowledged is not None else len(payload)
        
        # Subtrair latência de rede do tempo total para melhor precisão
        # Estimativa: tempo de resposta HTTP é ~latência
        if dt > 0.1:  # Só ajustar se tempo for significativo
            dt = max(0.01, dt - 0.05)  # Subtrair ~50ms de overhead
        
        out["upload_mbps"] = bytes_to_mbps(sent, dt)
        out["upload_seconds"] = round(dt, 3)
        out["upload_bytes"] = sent
    except Exception as e:
        out["upload_error"] = str(e)
        print(f"[agent] speedtest upload error: {e}")

    return out


def get_host_name() -> str:
    return platform.node() or os.getenv("COMPUTERNAME", "unknown-host")


def check_and_update(server: str, token: Optional[str]) -> bool:
    """Verifica se há atualização disponível e faz download se necessário.
    Retorna True se atualizou (requer restart), False caso contrário.
    """
    try:
        headers = {"X-Agent-Token": token} if token else {}
        url = f"{server}/api/agent/version"
        
        # Verificar versão disponível no servidor
        r = requests.get(url, headers=headers, timeout=10)
        if not r.ok:
            return False
        
        data = r.json()
        server_version = str(data.get("version", "")).strip()
        
        if not server_version or server_version == AGENT_VERSION:
            return False
        
        print(f"[agent] Nova versão disponível: {server_version} (atual: {AGENT_VERSION})")
        
        # Baixar nova versão
        download_url = f"{server}/api/agent/download"
        r = requests.get(download_url, headers=headers, timeout=60, stream=True)
        r.raise_for_status()
        
        # Salvar como arquivo temporário
        agent_path = Path(__file__)
        temp_path = agent_path.parent / f"agent_new_{server_version}.py"
        
        with open(temp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
        
        # Verificar se o arquivo baixado é válido (compilação Python)
        try:
            import py_compile
            py_compile.compile(str(temp_path), doraise=True)
        except Exception as e:
            print(f"[agent] Arquivo baixado inválido: {e}")
            temp_path.unlink()
            return False
        
        # Fazer backup do arquivo atual
        backup_path = agent_path.parent / f"agent_backup_{AGENT_VERSION}.py"
        if agent_path.exists():
            import shutil
            shutil.copy2(agent_path, backup_path)
        
        # Substituir arquivo atual
        import shutil
        shutil.move(str(temp_path), str(agent_path))
        
        print(f"[agent] Atualizado para versão {server_version}. Reiniciando...")
        return True
        
    except Exception as e:
        print(f"[agent] Erro ao verificar/baixar atualização: {e}")
        return False


def _state_path() -> Path:
    return Path(__file__).parent / "agent_state.json"


def _load_state() -> Dict[str, Any]:
    p = _state_path()
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _save_state(state: Dict[str, Any]) -> None:
    try:
        _state_path().write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_or_create_agent_id() -> str:
    """
    Gera um agent_id único baseado no hostname da máquina.
    Isso garante que cada PC tenha um ID diferente, mesmo se os arquivos forem copiados.
    """
    import hashlib
    
    # Usar hostname como base para gerar ID único por máquina
    hostname = get_host_name()
    
    # Verificar se já existe um agent_id salvo para este hostname
    data = _load_state()
    saved_hostname = data.get("hostname") if isinstance(data, dict) else None
    saved_agent_id = data.get("agent_id") if isinstance(data, dict) else None
    
    # Se o hostname mudou ou não existe agent_id, gerar novo
    if saved_hostname != hostname or not saved_agent_id:
        # Gerar ID único baseado no hostname + timestamp + random
        unique_string = f"{hostname}-{time.time()}-{uuid.uuid4()}"
        agent_id = hashlib.sha256(unique_string.encode()).hexdigest()[:32]
        
        state = data if isinstance(data, dict) else {}
        state["agent_id"] = agent_id
        state["hostname"] = hostname
        _save_state(state)
        
        print(f"[agent] Novo agent_id gerado para hostname '{hostname}': {agent_id}")
        return agent_id
    
    # Retornar agent_id existente para este hostname
    return str(saved_agent_id)


def register_agent(server: str, agent_id: str, host: str, token: Optional[str]) -> Dict[str, Any]:
    url = f"{server}/api/agents/register"
    try:
        r = requests.post(url, json={"agent_id": agent_id, "host": host, "token": token}, timeout=10)
        if r.status_code == 200:
            return r.json() if r.headers.get("content-type", "").lower().startswith("application/json") else {"ok": False, "reason": "invalid_response"}
        return {"ok": False, "reason": f"http_{r.status_code}", "detail": (r.text or "")[:200]}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def fetch_server_config(server: str, site: str, token: Optional[str]) -> Optional[Dict[str, Any]]:
    url = f"{server}/api/agents/{site}/config"
    headers = {"X-Agent-Token": token} if token else {}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"[agent] config HTTP {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"[agent] config error: {e}")
        return None


def post_report(server: str, site: str, token: Optional[str], payload: Dict[str, Any]) -> bool:
    url = f"{server}/api/agents/{site}/report"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Agent-Token"] = token
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"[agent] report ok: {r.json()}")
            return True
        else:
            print(f"[agent] report HTTP {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"[agent] report error: {e}")
        return False


def run_once(cfg: Dict[str, Any]) -> None:
    server: str = cfg["server"]
    token: Optional[str] = cfg.get("token")

    host = get_host_name()
    agent_id = load_or_create_agent_id()
    reg = register_agent(server, agent_id, host, token)
    if not bool(reg.get("ok")):
        print(f"[agent] register denied: {reg}")
        return
    site = str(reg.get("site") or "").strip()
    if not site:
        print(f"[agent] register missing site: {reg}")
        return

    # 1) Obter lista de câmeras do servidor (ou fallback para config local)
    conf = fetch_server_config(server, site, token)
    cameras: List[Dict[str, Any]] = []
    speed_enabled = bool(cfg.get("speedtest"))
    # Aumentar tamanho padrão para melhor precisão (5MB download, 2MB upload)
    speed_dl = int(cfg.get("speed_download_bytes", 5 * 1024 * 1024))
    speed_ul = int(cfg.get("speed_upload_bytes", 2 * 1024 * 1024))
    speedtest_interval_sec = int(os.getenv("AGENT_SPEEDTEST_INTERVAL_SEC", "60"))
    inet_enabled = os.getenv("AGENT_INET_SPEEDTEST", "1").strip().lower() in ("1", "true", "yes")
    inet_interval_sec = int(os.getenv("AGENT_INET_SPEEDTEST_INTERVAL_SEC", "300"))
    if conf and isinstance(conf, dict) and conf.get("speedtest_interval_sec") is not None:
        try:
            speedtest_interval_sec = int(conf.get("speedtest_interval_sec"))
        except Exception:
            pass
    if conf and isinstance(conf, dict):
        if conf.get("interval_sec") is not None:
            try:
                cfg["interval_sec"] = int(conf.get("interval_sec"))
            except Exception:
                pass
        if "speedtest" in conf:
            speed_enabled = bool(conf.get("speedtest"))
        if conf.get("speed_download_bytes") is not None:
            try:
                speed_dl = int(conf.get("speed_download_bytes"))
            except Exception:
                pass
        if conf.get("speed_upload_bytes") is not None:
            try:
                speed_ul = int(conf.get("speed_upload_bytes"))
            except Exception:
                pass
    if conf and isinstance(conf.get("cameras"), list):
        for c in conf["cameras"]:
            if isinstance(c, dict) and c.get("ip"):
                cameras.append({"name": c.get("name"), "ip": c.get("ip")})
    else:
        # fallback local
        for c in cfg.get("cameras", []):
            if isinstance(c, dict) and c.get("ip"):
                cameras.append({"name": c.get("name"), "ip": c.get("ip")})

    # 2) Testes de rede
    net = test_network()

    # 2.0) Internet speedtest (opcional) - cache
    state = _load_state()
    last_inet_at = state.get("last_inet_speedtest_at")
    last_inet = state.get("last_inet_speedtest") if isinstance(state.get("last_inet_speedtest"), dict) else None
    run_inet = False
    try:
        now = time.time()
        # Se a última tentativa deu erro, tentar novamente imediatamente.
        if isinstance(last_inet, dict) and last_inet.get("inet_error"):
            run_inet = True
        elif not isinstance(last_inet_at, (int, float)):
            run_inet = True
        else:
            run_inet = (now - float(last_inet_at)) >= float(max(30, inet_interval_sec))
    except Exception:
        run_inet = True

    if inet_enabled and run_inet:
        inet = internet_speedtest()
        net.update(inet)
        state["last_inet_speedtest"] = inet
        # Só cacheia o timestamp quando não houve erro, para tentar novamente no próximo ciclo.
        if not inet.get("inet_error"):
            state["last_inet_speedtest_at"] = time.time()
        _save_state(state)
    elif isinstance(last_inet, dict):
        net.update(last_inet)

    # 2.1) Speedtest (opcional) - cache para não rodar a cada ciclo
    state = _load_state()
    last_st_at = state.get("last_speedtest_at")
    last_st = state.get("last_speedtest") if isinstance(state.get("last_speedtest"), dict) else None
    run_st = False
    try:
        now = time.time()
        if not isinstance(last_st_at, (int, float)):
            run_st = True
        else:
            run_st = (now - float(last_st_at)) >= float(max(5, speedtest_interval_sec))
    except Exception:
        run_st = True

    if speed_enabled and run_st:
        st = speedtest(server, speed_dl, speed_ul, token)
        net.update(st)
        state["last_speedtest_at"] = time.time()
        state["last_speedtest"] = st
        _save_state(state)
    elif isinstance(last_st, dict):
        net.update(last_st)

    # 3) Pingar cameras com retry, validação melhorada e rastreamento por MAC
    cam_reports: List[Dict[str, Any]] = []
    mac_tracking_enabled = os.getenv("AGENT_MAC_TRACKING", "1").strip().lower() in ("1", "true", "yes")
    mac_cache = state.get("camera_mac_cache", {})
    mac_cache_updated = False
    
    for c in cameras:
        ip = c.get("ip")
        name = c.get("name")
        cam_id = c.get("id") or name or ip  # Identificador único
        
        # Usar 4 pings com 2 retries para maior confiabilidade
        reachable, avg_ms, loss, _out = ping_ip(ip, count=4, timeout_ms=1000, retry=2)
        
        # Validação adicional: se latência muito alta (>500ms) em rede local, marcar como suspeito
        suspicious = False
        if reachable and avg_ms is not None and avg_ms > 500:
            if ip.startswith(("192.168.", "10.", "172.")):
                suspicious = True
        
        # Sistema de rastreamento por MAC address
        mac_address = None
        ip_changed = False
        new_ip = None
        
        if mac_tracking_enabled:
            # Se câmera está online, obter e cachear MAC address
            if reachable:
                mac_address = get_mac_address(ip)
                if mac_address:
                    # Atualizar cache
                    if str(cam_id) not in mac_cache or mac_cache[str(cam_id)].get("mac") != mac_address:
                        mac_cache[str(cam_id)] = {
                            "mac": mac_address,
                            "last_ip": ip,
                            "last_seen": time.time()
                        }
                        mac_cache_updated = True
                        print(f"[agent] Cached MAC {mac_address} for camera {name} ({ip})")
            
            # Se câmera está offline mas temos MAC em cache, tentar encontrar novo IP
            elif not reachable and str(cam_id) in mac_cache:
                cached_mac = mac_cache[str(cam_id)].get("mac")
                if cached_mac:
                    print(f"[agent] Camera {name} offline at {ip}, searching by MAC {cached_mac}...")
                    
                    # Extrair prefixo da rede do IP atual
                    ip_parts = ip.split(".")
                    if len(ip_parts) == 4:
                        network_prefix = ".".join(ip_parts[:3]) + "."
                        
                        # Scan limitado (30 segundos max)
                        new_ip = scan_network_for_mac(cached_mac, network_prefix, timeout_sec=30)
                        
                        if new_ip and new_ip != ip:
                            print(f"[agent] Camera {name} found at new IP: {new_ip} (was {ip})")
                            ip_changed = True
                            
                            # Re-testar no novo IP
                            reachable, avg_ms, loss, _out = ping_ip(new_ip, count=4, timeout_ms=1000, retry=2)
                            
                            if reachable:
                                # Atualizar cache com novo IP
                                mac_cache[str(cam_id)]["last_ip"] = new_ip
                                mac_cache[str(cam_id)]["last_seen"] = time.time()
                                mac_cache_updated = True
                                
                                # Atualizar IP para o relatório
                                ip = new_ip
        
        cam_reports.append({
            "name": name,
            "ip": ip,
            "status": "up" if reachable else "down",
            "latency_ms": avg_ms,
            "packet_loss": loss,
            "suspicious": suspicious,
            "mac_address": mac_address,
            "ip_changed": ip_changed,
            "old_ip": c.get("ip") if ip_changed else None
        })
    
    # Salvar cache de MAC atualizado
    if mac_cache_updated:
        state["camera_mac_cache"] = mac_cache
        _save_state(state)

    # 4) Montar payload
    payload = {
        "site": site,
        "host": host,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "network": net,
        "cameras": cam_reports,
        "agent": {"version": AGENT_VERSION, "interval_sec": cfg.get("interval_sec", DEFAULT_INTERVAL)}
    }

    # 5) Enviar
    post_report(server, site, token, payload)


def main() -> None:
    cfg = load_agent_config()
    loop = cfg.get("loop", False)
    interval_sec = cfg.get("interval_sec", DEFAULT_INTERVAL)
    server = cfg.get("server", "")
    token = cfg.get("token")
    
    # Verificar atualização na inicialização
    update_check_interval = 300  # 5 minutos
    last_update_check = 0
    
    if loop:
        while True:
            try:
                # Verificar atualização periodicamente
                now = time.time()
                if now - last_update_check >= update_check_interval:
                    if check_and_update(server, token):
                        # Atualização baixada, reiniciar processo
                        print("[agent] Reiniciando após atualização...")
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                    last_update_check = now
                
                run_once(cfg)
            except Exception as e:
                print(f"[agent] error in run_once: {e}")
            time.sleep(interval_sec)
    else:
        # Modo single-run: verificar atualização antes de executar
        if check_and_update(server, token):
            print("[agent] Atualização aplicada. Execute novamente para usar nova versão.")
        else:
            run_once(cfg)


if __name__ == "__main__":
    main()
