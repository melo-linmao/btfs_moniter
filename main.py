# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import paramiko
import yaml
import argparse
import time
import json
import requests


class Btfs_Moniter():
    def __init__(self):
        self.moniter_server = paramiko.SSHClient()
        #self.sftp = self.moniter_server.open_sftp()
        moniter_conf = yaml.load(open("./conf/moniter_server.yaml"), Loader=yaml.SafeLoader)
        self.user = moniter_conf["moniter_server"]["user"]
        self.host = moniter_conf["moniter_server"]["host"]
        self.port = moniter_conf["moniter_server"]["port"]
        self.key_file = moniter_conf["moniter_server"]["keyfile"]
        self.build_path = moniter_conf["moniter_server"]["keyfile"]
        self.btfs_scan_case_url = moniter_conf["moniter_server"]["moniter_case"]["btfs_scan"]
        self.btfs_storage3_case_url = moniter_conf["moniter_server"]["moniter_case"]["btfs_storage3"]
        self.btfs_dashboard_case_url = moniter_conf["moniter_server"]["moniter_case"]["btfs_dashboard"]
        self.alert_url = moniter_conf["moniter_server"]["alert_url"]
        self.alert_channel = moniter_conf["moniter_server"]["alert_channel"]

    def server_connect(self):
        # 连接监控服务器
        self.moniter_server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.moniter_server.connect(hostname=self.host, username=self.user, port=self.port, key_filename=self.key_file)
        except Exception as e:
            print("can not connect moniter server", e)
            print(e)
        print(self.host + " " + " " + "connect ok")

    def server_close(self):
        #断开测试服务器
        self.moniter_server.close()
        print('moniter server has been closed')

    def exec_moniter_command(self, cmd, args=None, timeout=None):
        _, stdout, stderr = self.moniter_server.exec_command(cmd, timeout=timeout)
        out_bytes = stdout.read().replace(bytes('\n', encoding="utf-8"), bytes(' ', encoding="utf-8"))
        err_bytes = stderr.read().replace(bytes('\n', encoding="utf-8"), bytes(' ', encoding="utf-8"))
        out = str(out_bytes, 'utf-8')
        err = str(err_bytes, 'utf-8')
        # strip out trailing spaces from out and err
        out = out.rstrip()
        err = err.rstrip()
        return out, err

    def moniter_run(self, moniter_case, output):
        self.moniter_case = moniter_case
        if (moniter_case == "btfs_scan"):
            self.case_url = self.btfs_scan_case_url
        if (moniter_case == "btfs_storage3"):
            self.case_url = self.btfs_storage3_case_url
        if (moniter_case == "btfs_dashboard"):
            self.case_url = self.btfs_dashboard_case_url
        res,err = self.exec_moniter_command('date +%Y-%m-%d-%H-%M-%S')
        moniter_time = res
        self.report_name = moniter_case + '-' + moniter_time
        res, err = self.exec_moniter_command('apifox run ' + self.case_url + ' -r ' + output + ',html,json' + ' --out-file ' + self.report_name)
        if err == '':
            print("moniter task finished,you can check the report to use http://52.25.222.175:8000/")
        else:
            print(err)

    def result_check(self):
        try:
            res, err = self.exec_moniter_command('cat' + ' ./apifox-reports/' + self.report_name + '.json')
            if err != '':
                print(err)
                config_json = None
            else:
                config_json = json.loads(res)
                failures_json = config_json['result']['failures']
                #print(len(failures_json))
                if len(failures_json) != 0:
                    self.send_alert_message(failures_json)
                else:
                    print('monitor task finished and there is no alert message you need to foucs on')
        except Exception as e:
            raise Exception(e)

    def send_alert_message(self, failure_json):
        moniter_report = "http://52.25.222.175:8000/" + self.report_name + ".html"
        moniter_case = str(self.moniter_case)
        alert_message = {}
        alert_msg = {}
        alert_message["moniter_report"] = moniter_report
        alert_message["moniter_case"] = moniter_case
        alert_message["failures"] = failure_json
        alert_msg["channel"] = self.alert_channel
        alert_msg["failure_json"] = alert_message
        alert_msg = json.dumps(alert_msg)
        respons = requests.request(method='POST', url=self.alert_url, json=alert_msg)
        print(respons)
        #self.exec_moniter_command('echo')
        #print(alert_message["moniter_report"])
        #print(alert_message["moniter_case"])





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", '--moniter_case', default="btfs_scan", help="input zhe moniter type.you can choose one of the btfs_scan,btfs_storage3 or btfs_dashboard")
    parser.add_argument("-o", '--output', default="cli", help="input zhe report type,you can choose html or json")
    parse_args = parser.parse_args()
    moniter_case = parse_args.moniter_case
    output = parse_args.output
    btfs_moniter = Btfs_Moniter()
    btfs_moniter.server_connect()
    btfs_moniter.moniter_run(moniter_case, output)
    btfs_moniter.result_check()
    btfs_moniter.server_close()




