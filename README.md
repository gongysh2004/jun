# jun

```
pip3 install "uvicorn[standard]"
pip3 install fastapi
pip3 install kubernetes


uvicorn usage:app --host=127.0.0.1 --port=8000 --reload
```

https://www.cnblogs.com/CharmCode/p/14191108.html

https://github.com/kubernetes-client/python.git
curl --cert /etc/kubernetes/pki/apiserver-kubelet-client.crt \
    --key /etc/kubernetes/pki/apiserver-kubelet-client.key \
        -k https://lb.kubesphere.local:6443/api/v1/pods