
- [1. install kubernetes](#1-install-kubernetes)
  - [1.1. prepare host packages](#11-prepare-host-packages)
  - [1.2. prepare cluster definition file](#12-prepare-cluster-definition-file)
  - [1.3. install cluster](#13-install-cluster)
  - [1.4. patch daemonset not to install on edgenode](#14-patch-daemonset-not-to-install-on-edgenode)
- [2. add edgenode](#2-add-edgenode)
  - [2.1. deal with node](#21-deal-with-node)
  - [2.2. install containerd](#22-install-containerd)
  - [2.3. join node](#23-join-node)
  - [2.4. enable kubectl log](#24-enable-kubectl-log)
- [3. test](#3-test)
  - [3.1. deploy pod](#31-deploy-pod)
  - [3.2. connect data plane for edgenode](#32-connect-data-plane-for-edgenode)
- [4. python cli sdk](#4-python-cli-sdk)
- [5. resource usage](#5-resource-usage)
- [6. References](#6-references)


# 1. install kubernetes
## 1.1. prepare host packages
```
apt-get install -y conntrack socat net-tools ipvsadm ipset ebtables chrony openssl

wget https://github.com/kubeedge/kubeedge/releases/download/v1.15.1/keadm-v1.15.1-linux-amd64.tar.gz
tar xzvf keadm-v1.15.1-linux-amd64.tar.gz 
mv keadm-v1.15.1-linux-amd64/keadm/keadm /usr/local/bin/


```

## 1.2. prepare cluster definition file

```
cat >kk.yaml <<EOF
apiVersion: kubekey.kubesphere.io/v1alpha2
kind: Cluster
metadata:
  name: sample
spec:
  hosts:
  - {name: compute3, address: 192.168.50.13, internalAddress: 192.168.50.13, privateKeyPath: "~/.ssh/id_rsa"}
  roleGroups:
    etcd:
    - compute3
    control-plane: 
    - compute3
    worker:
    - compute3
  controlPlaneEndpoint:
    ## Internal loadbalancer for apiservers 
    # internalLoadbalancer: haproxy

    domain: lb.kubesphere.local
    address: ""
    port: 6443
  kubernetes:
    version: v1.22.1
    clusterName: cluster.local
    autoRenewCerts: true
    containerManager: containerd
  etcd:
    type: kubekey
  network:
    plugin: calico
    kubePodsCIDR: 10.233.64.0/18
    kubeServiceCIDR: 10.233.0.0/18
    ## multus support. https://github.com/k8snetworkplumbingwg/multus-cni
    multusCNI:
      enabled: false
  registry:
    privateRegistry: ""
    namespaceOverride: ""
    registryMirrors: []
    insecureRegistries: []
  addons: []

---
apiVersion: installer.kubesphere.io/v1alpha1
kind: ClusterConfiguration
metadata:
  name: ks-installer
  namespace: kubesphere-system
  labels:
    version: v3.4.1
spec:
  persistence:
    storageClass: ""
  authentication:
    jwtSecret: ""
  local_registry: ""
  # dev_tag: ""
  etcd:
    monitoring: false
    endpointIps: localhost
    port: 2379
    tlsEnable: true
  common:
    core:
      console:
        enableMultiLogin: true
        port: 30880
        type: NodePort
    # apiserver:
    #  resources: {}
    # controllerManager:
    #  resources: {}
    redis:
      enabled: false
      enableHA: false
      volumeSize: 2Gi
    openldap:
      enabled: false
      volumeSize: 2Gi
    minio:
      volumeSize: 20Gi
    monitoring:
      # type: external
      endpoint: http://prometheus-operated.kubesphere-monitoring-system.svc:9090
      GPUMonitoring:
        enabled: false
    gpu:
      kinds:
      - resourceName: "nvidia.com/gpu"
        resourceType: "GPU"
        default: true
    es:
      # master:
      #   volumeSize: 4Gi
      #   replicas: 1
      #   resources: {}
      # data:
      #   volumeSize: 20Gi
      #   replicas: 1
      #   resources: {}
      enabled: false
      logMaxAge: 7
      elkPrefix: logstash
      basicAuth:
        enabled: false
        username: ""
        password: ""
      externalElasticsearchHost: ""
      externalElasticsearchPort: ""
    opensearch:
      # master:
      #   volumeSize: 4Gi
      #   replicas: 1
      #   resources: {}
      # data:
      #   volumeSize: 20Gi
      #   replicas: 1
      #   resources: {}
      enabled: true
      logMaxAge: 7
      opensearchPrefix: whizard
      basicAuth:
        enabled: true
        username: "admin"
        password: "admin"
      externalOpensearchHost: ""
      externalOpensearchPort: ""
      dashboard:
        enabled: false
  alerting:
    enabled: false
    # thanosruler:
    #   replicas: 1
    #   resources: {}
  auditing:
    enabled: false
    # operator:
    #   resources: {}
    # webhook:
    #   resources: {}
  devops:
    enabled: false
    jenkinsCpuReq: 0.5
    jenkinsCpuLim: 1
    jenkinsMemoryReq: 4Gi
    jenkinsMemoryLim: 4Gi
    jenkinsVolumeSize: 16Gi
  events:
    enabled: false
    # operator:
    #   resources: {}
    # exporter:
    #   resources: {}
    ruler:
      enabled: true
      replicas: 2
    #   resources: {}
  logging:
    enabled: false
    logsidecar:
      enabled: true
      replicas: 2
      # resources: {}
  metrics_server:
    enabled: true
  monitoring:
    storageClass: ""
    node_exporter:
      port: 9100
      # resources: {}
    # kube_rbac_proxy:
    #   resources: {}
    # kube_state_metrics:
    #   resources: {}
    # prometheus:
    #   replicas: 1
    #   volumeSize: 20Gi
    #   resources: {}
    #   operator:
    #     resources: {}
    # alertmanager:
    #   replicas: 1
    #   resources: {}
    # notification_manager:
    #   resources: {}
    #   operator:
    #     resources: {}
    #   proxy:
    #     resources: {}
    gpu:
      nvidia_dcgm_exporter:
        enabled: false
        # resources: {}
  multicluster:
    clusterRole: none
  network:
    networkpolicy:
      enabled: false
    ippool:
      type: none
    topology:
      type: none
  openpitrix:
    store:
      enabled: false
  servicemesh:
    enabled: false
    istio:
      components:
        ingressGateways:
        - name: istio-ingressgateway
          enabled: false
        cni:
          enabled: false
  edgeruntime:
    enabled: true
    kubeedge:
      enabled: true
      cloudCore:
        cloudHub:
          advertiseAddress:
            - "192.168.50.13"
        service:
          cloudhubNodePort: "30000"
          cloudhubQuicNodePort: "30001"
          cloudhubHttpsNodePort: "30002"
          cloudstreamNodePort: "30003"
          tunnelNodePort: "30004"
        # resources: {}
        # hostNetWork: true
      iptables-manager:
        enabled: true
        mode: "external"
        # resources: {}
      # edgeService:
      #   resources: {}
  gatekeeper:
    enabled: false
    # controller_manager:
    #   resources: {}
    # audit:
    #   resources: {}
  terminal:
    timeout: 600

EOF
```

## 1.3. install cluster
```
curl -sfL https://get-kk.kubesphere.io | VERSION=v3.0.13 sh -
chmod +x kk
./kk version --show-supported-k8s


# ./kk create cluster --with-kubernetes v1.21.14  --with-kubesphere v3.4.1 --container-manager containerd 

./kk create cluster -f kk.yaml -y

```

Console: http://192.168.50.13:30880
Account: admin
Password: P@88w0rd


## 1.4. patch daemonset not to install on edgenode
```

NoShedulePatchJson='{"spec":{"template":{"spec":{"affinity":{"nodeAffinity":{"requiredDuringSchedulingIgnoredDuringExecution":{"nodeSelectorTerms":[{"matchExpressions":[{"key":"node-role.kubernetes.io/edge","operator":"DoesNotExist"}]}]}}}}}}}'

   

nses=("kube-system" "calico-system")
lengthj=${#nses[@]}




DaemonSets=("nodelocaldns" "kube-proxy" "calico-node" "csi-node-driver")



length=${#DaemonSets[@]}

for ((j=0;i<lengthj;j++));
do
ns=${nses[$j]}

for((i=0;i<length;i++));  

do

         ds=${DaemonSets[$i]}

        echo "Patching resources:DaemonSet/${ds}" in ns:"$ns",

        kubectl -n $ns patch DaemonSet/${ds} --type merge --patch "$NoShedulePatchJson"

        sleep 1

done
done

```

# 2. add edgenode

## 2.1. deal with node

```
sed -i '/^hosts:/d'  /etc/nsswitch.conf
sed -i '$ a hosts:          dns files mdns4_minimal [NOTFOUND=return]' /etc/nsswitch.conf
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
sysctl -p | grep ip_forward
```

## 2.2. install containerd

```
wget https://github.com/kubeedge/kubeedge/releases/download/v1.15.1/keadm-v1.15.1-linux-amd64.tar.gz
tar xzvf keadm-v1.15.1-linux-amd64.tar.gz 
mv keadm-v1.15.1-linux-amd64/keadm/keadm /usr/local/bin/


# Install containerd
wget https://github.com/containerd/containerd/releases/download/v1.7.11/containerd-1.7.11-linux-amd64.tar.gz -O containerd.tgz
tar Cxzvf /usr/local containerd.tgz
mkdir -p /usr/local/lib/systemd/system/
wget https://raw.githubusercontent.com/containerd/containerd/main/containerd.service -O /usr/local/lib/systemd/system/containerd.service
systemctl daemon-reload
systemctl enable --now containerd
# sed -i 's/systemd_cgroup = false/systemd_cgroup = true/' /etc/containerd/config.toml


wget https://github.com/opencontainers/runc/releases/download/v1.1.10/runc.amd64
install -m 755 runc.amd64 /usr/local/sbin/runc

wget https://github.com/containernetworking/plugins/releases/download/v1.4.0/cni-plugins-linux-amd64-v1.4.0.tgz -O cni.tgz
mkdir -p /opt/cni/bin
tar Cxzvf /opt/cni/bin cni.tgz

cat > /etc/cni/net.d/10-containerd-net.conflist <<EOF
{
     "cniVersion": "1.0.0",
     "name": "containerd-net",
     "plugins": [
       {
         "type": "bridge",
         "bridge": "cni0",
         "isGateway": true,
         "ipMasq": true,
         "promiscMode": true,
         "ipam": {
           "type": "host-local",
           "ranges": [
             [{
               "subnet": "10.10.11.0/24"
             }]
           ],
           "routes": [
             { "dst": "0.0.0.0/0" },
             { "dst": "::/0" }
           ]
         }
       },
       {
         "type": "portmap",
         "capabilities": {"portMappings": true}
       }
     ]
    }
EOF

wget https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.29.0/crictl-v1.29.0-linux-amd64.tar.gz -O crictl.tgz
tar Cxzvf /usr/local/bin crictl.tgz

cat > /etc/crictl.yaml <<EOF
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 2
debug: false
pull-image-on-create: false

EOF
crictl info
```

## 2.3. join node
```

systemctl stop edgecore.service
systemctl stop containerd
rm -rf /var/lib/containerd/
systemctl start containerd
rm -rf /etc/kubeedge

token=$(ssh 192.168.50.13 /usr/local/bin/keadm gettoken)


arch=$(uname -m); if [[ $arch != x86_64 ]]; then arch='arm64'; fi;  curl -LO https://kubeedge.pek3b.qingstor.com/bin/v1.13.0/$arch/keadm-v1.13.0-linux-$arch.tar.gz  && tar xvf keadm-v1.13.0-linux-$arch.tar.gz && chmod +x keadm && ./keadm join --kubeedge-version=1.13.0 --cloudcore-ipport=192.168.50.13:30000 --quicport 30001 --certport 30002 --tunnelport 30004 --edgenode-name $(hostname)  --edgenode-ip 192.168.50.14 --token $token


#kubectl taint nodes edgenode-7sjo node-role.kubernetes.io/edge:NoSchedule-

```

## 2.4. enable kubectl log
```

sed -i '/edgeStream:/!b;n;c\    enable: true' /etc/kubeedge/config/edgecore.yaml
systemctl restart edgecore.service

```

# 3. test

## 3.1. deploy pod

```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: busyboxedge
spec:
  containers:
  - name: busyboxedge
    image: busybox:latest
    command: ["/bin/sh", "-ec", "while :; do echo 'EDGE'; sleep 5 ; done"]
    resources:
      requests:
        memory: "1024Mi"
        cpu: "2"
      limits:
        memory: "1024Mi"
        cpu: "2"
    ports:
    - containerPort: 80
  nodeSelector:
    "node-role.kubernetes.io/edge": ""
EOF


cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: busyhost
spec:
  containers:
  - name: busyhost
    image: busybox:latest
    command: ["/bin/sh", "-ec", "while :; do echo '.+'; sleep 5 ; done"]
    resources:
      requests:
        memory: "1024Mi"
        cpu: "2"
      limits:
        memory: "1024Mi"
        cpu: "2"
    ports:
    - containerPort: 80
  nodeSelector:
    "node-role.kubernetes.io/worker": ""
EOF

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: busy-deployment
  labels:
    app: busy
spec:
  replicas: 2
  selector:
    matchLabels:
      app: busy
  template:
    metadata:
      labels:
        app: busy
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - busy
            topologyKey: "kubernetes.io/hostname"
      containers:
      - name: busy
        image: busybox:latest
        command: ["/bin/sh", "-ec", "while :; do echo '.+'; sleep 5 ; done"]
        resources:
          requests:
            memory: "1024Mi"
            cpu: "2"
          limits:
            memory: "1024Mi"
            cpu: "2"
      nodeSelector:
        "node-role.kubernetes.io/edge": ""
EOF

kubectl scale --replicas=2 deployment/busy-deployment
```



```
kubectl logs busyboxedge
kubectl logs busyhost
```

## 3.2. connect data plane for edgenode
```
brctl addif cn0 eth3
ip r add 10.10.11.0/24 via 10.10.11.1 dev cni0 onlink

brctl addif cn0 eth3
ip r add 10.10.12.0/24 via 10.10.12.1 dev cni0 onlink
```


# 4. python cli sdk
https://github.com/kubernetes-client/python

# 5. resource usage
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/nodes" | jq
https://github.com/kubernetes/design-proposals-archive/blob/main/instrumentation/resource-metrics-api.md
http://172.16.30.21/mec/kube-placement/blob/master/README.md
https://zhc3o5gmf9.feishu.cn/docx/Z80CdT7vUo760hxU8IIcbOoLnLd

# 6. References
- https://release-1-15.docs.kubeedge.io/docs/welcome/getting-started
- https://www.kubesphere.io/zh/docs/v3.4/quick-start/all-in-one-on-linux/
- https://www.kubesphere.io/zh/docs/v3.4/installing-on-linux/cluster-operation/add-edge-nodes/
- https://www.kubesphere.io/zh/docs/v3.4/pluggable-components/kubeedge/
- https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/