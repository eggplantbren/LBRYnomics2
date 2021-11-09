import requests
import time

def lbrycrd_nodes():
    now = time.time()
    result = None

    try:
        nodes = requests.post("https://nodes.madiator.com/api/get_nodes")
        nodes = nodes.json()
        nodes = [node for node in nodes if node["last_seen"] >= (now - 3600.0)]
        result = len(nodes)
    except:
        pass

    if result == 0:
        result = None
    return result