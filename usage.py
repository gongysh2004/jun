
"""


# curl -s http://localhost:8000/usage_with_tasks | jq
{
  "usage": {
    "compute2": {
      "allocable_cpu": 32,
      "allocable_memory": 62,
      "allocated_cpu": 1,
      "allocated_memory": 1
    },
    "edgenode-7sjo": {
      "allocable_cpu": 32,
      "allocable_memory": 62
    }
  },
  "tasks": [
    {
      "name": "task-a",
      "host": "compute2",
      "ip": "10.10.12.10"
    }
  ]
}


# curl -s -X 'POST'   'http://127.0.0.1:8000/tasks-a'   -H 'accept: application/json'   -d '' | jq
{
  "action": "deleted"
}

# curl -s -X 'POST'   'http://127.0.0.1:8000/tasks-a'   -H 'accept: application/json'   -d '' | jq
{
  "action": "started"
}

"""

import json
from os import path

import yaml

from kubernetes import config, dynamic, client, utils
from kubernetes.client import api_client, exceptions



from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "自动任务调度系统"}


@app.get("/usage_with_tasks")
def get_usage_with_tasks():
     return {'usage': _caculate_usage(), 'tasks': _list_tasks()}


@app.post("/tasks-a")
async def start_or_delete_task_a():
    res = _start_or_delete_task('task-a')
    return {"action": res}


@app.post("/tasks-b")
async def start_or_delete_task_b():
    res = _start_or_delete_task('task-b')
    return {"action": res}


def _list_tasks():
    config.load_kube_config()
    k8s_core_v1 = client.CoreV1Api()
    res_pods = k8s_core_v1.list_namespaced_pod(namespace="default")
    pods = []
    for pod in res_pods.items:
        print(f'pod: {pod.metadata.name}, {pod.status.pod_ip}, {pod.spec.node_name}')
        if pod.metadata.name in ('task-a', 'task-b'):
            pods.append({'name': pod.metadata.name, 'host': pod.spec.node_name, 'ip':  pod.status.pod_ip})
    return pods


def _start_or_delete_task(name: str):
    task_yml = f'tasks/{name}.yml'
    xx = _is_existed_task(name)
    res = "deleted"
    if not xx:
        _start_task(task_yml)
        res = "started"
    else:
        _delete_task(name)
    return res


def _start_task(task_yaml: str):
    config.load_kube_config()
    with open(path.join(path.dirname(__file__), task_yaml)) as f:
        task = yaml.safe_load(f)
        k8s_core_v1 = client.CoreV1Api()
        resp = k8s_core_v1.create_namespaced_pod(
            body=task, namespace="default")
        print(f"task created. Status='{resp.metadata.name}'")
    return resp


def _is_existed_task(task_name: str):
    config.load_kube_config()
    k8s_core_v1 = client.CoreV1Api()
    try:
        k8s_core_v1.read_namespaced_pod(name=task_name, namespace='default')
    except exceptions.ApiException:
        return False
    return True


def _delete_task(task_name: str):
    config.load_kube_config()
    k8s_core_v1 = client.CoreV1Api()
    pod = k8s_core_v1.delete_namespaced_pod(namespace="default", name=task_name)
    print(f'deleted: {pod.metadata.name}')


def _mem_value(mem_str):
    mem_int = 0
    if (mem_str.upper().endswith("KI")):
        mem_int = int(mem_str[:-2])/1024.0/1024.0 # to G
    elif(mem_str.upper().endswith("GI")):
        mem_int = int(mem_str[:-2])
    elif(mem_str.upper().endswith("MI")):
        mem_int = int(mem_str[:-2])/1024.0
    else:
        mem_int = int(mem_str)/1024.0/1024.0/1024.0
    return int(mem_int)

def _cpu_value(cpu):
    cpu_int = 0
    if cpu.upper().endswith("N"):
        cpu_int=int(cpu[:-1])/1000000000.0
    elif cpu.upper().endswith("M"):
        cpu_int=int(cpu[:-1])/1000.0
    else:
        cpu_int=int(cpu)*1.0
    return int(cpu_int)


def _caculate_usage():
    # Creating a dynamic client
    d_client = dynamic.DynamicClient(
        api_client.ApiClient(configuration=config.load_kube_config())
    )

    # fetching the node api
    api = d_client.resources.get(api_version="v1", kind="Node")

    # Listing cluster nodes
    nodes_dict = {}
    for item in api.get().items:
        labels = item.metadata.labels
        if 'node-role.kubernetes.io/edge' in labels.to_dict():
            node_dict = {}
            node_dict["allocable_cpu"] = _cpu_value(item.status.allocatable.cpu)
            memory_str = str(item.status.allocatable.memory)
            node_dict["allocable_memory"] = _mem_value(memory_str)
            nodes_dict[item.metadata.name] = node_dict

    v1 = client.CoreV1Api()
    allocated_dic={}
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for item in ret.items:
        node_name = item.spec.node_name
        node_allocated_dict = allocated_dic.get(node_name,{})
        for c in item.spec.containers:
            if c.resources.limits:
                cpu = c.resources.limits.get('cpu', '0')
                mem = c.resources.limits.get('memory', '0')
                allocated_cpu = node_allocated_dict.get('allocated_cpu', 0)
                allocated_cpu += _cpu_value(cpu)
                node_allocated_dict['allocated_cpu'] = allocated_cpu
                allocated_memory = node_allocated_dict.get('allocated_memory', 0)
                allocated_memory += _mem_value(mem)
                node_allocated_dict['allocated_memory'] = allocated_memory
        allocated_dic[node_name] = node_allocated_dict
    for node_name, _node_dict in nodes_dict.items():
        _node_dict.update(allocated_dic.get(node_name, {}))
    return nodes_dict


if __name__ == "__main__1":
    _caculate_usage()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app='usage:app', host="0.0.0.0", port=8000, reload=True, log_level='debug')