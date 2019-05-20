import subprocess

from colorama import Fore
from colorama import Style


class Kubernetes:
    def __init__(self, kubeconfig):
        """
        Handle interactions with an environment's Kubernetes cluster
        """
        self.kubeconfig = kubeconfig

    def show_dashboard(self):
        """
        Show the environment's kubernetes dashboard
        :return:
        """
        secret_cmd = f"kubectl --kubeconfig {self.kubeconfig} -n kube-system get secret | grep eks-admin | awk '{{print $1}}'"
        ps_secret = subprocess.Popen(secret_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        secret = ps_secret.communicate()[0].decode("utf-8").strip()
        token_cmd = f"kubectl --kubeconfig {self.kubeconfig} -n kube-system describe secret {secret} | grep -E '^token' | cut -f2 -d':' | tr -d \" \""
        ps_token = subprocess.Popen(token_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        token = ps_token.communicate()[0].decode("utf-8").strip()
        print(f'{Fore.GREEN}HERE IS YOUR KUBERNETES DASHBOARD TOKEN: {Fore.BLUE}{token}{Style.RESET_ALL}')
        proxy_cmd = f"kubectl --kubeconfig {self.kubeconfig} proxy -p 8001"
        subprocess.Popen("open http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes"
                         "-dashboard:/proxy/", shell=True)
        subprocess.run(proxy_cmd, shell=True)
