#!/usr/bin/env python3

import sys
import json
import pprint

from pysros.exceptions import ModelProcessingError
from pysros.management import connect, sros
from pysros.pprint import Table
from pysros.pprint import printTree


credentials = {
    "host" : "172.18.67.201",
    "username" : "admin",
    "password" : "admin",
    "port" : 830,
    }

def get_connection(creds):
    try:
        if sros():
            connection_object = connect()
        else:
            connection_object = connect(
                host=creds["host"],
                username=creds["username"],
                password=creds["password"],
                port=creds["port"],
            )
        return connection_object

    except RuntimeError as error1:
        print("Failed to connect during creation of the connection object. Error:", error1, end="")
        sys.exit(101)

    except ModelProcessingError as error2:
        print("Failed to create YANG schema. Error:", error2, end="")
        sys.exit(102)

    except Exception as error3:
        print("Failed to connect. Error:", error3, end="")
        sys.exit(103)


def print_table(rows, cols):
    cols = [
        (10, "Name"),
        (10, "Type"),
        (20, "Peer IP"),
        (10, "Peer Group"),
        (8, "Peer AS"),
        (20, "Peer Status"),
    ]

    width = sum(
        [col[0] for col in cols]
    )

    table = Table("BGP neighbor list", cols, width=width)
    table.print(rows)



def get_vprn_base_bgp():
    conn_obj = get_connection(credentials)
    conf_path_list = [
        "/nokia-conf:configure/service/vprn",
        "/nokia-conf:configure/router",
    ]

    rows = []
    cols = []

    for path in conf_path_list:
        vrouter_type = path.rsplit("/", maxsplit=1)[-1]
        vrouter_config = conn_obj.running.get(path)

        if vrouter_type == "vprn":
            for vrtr_name in vrouter_config:
                vrtr_pair = [vrtr_name, vrouter_type]
                vrouter_bgp_neighbor = conn_obj.running.get('/nokia-conf:configure/service/vprn[service-name=%s]/bgp/neighbor' %vrtr_name)
                vrouter_bgp_group = conn_obj.running.get('/nokia-conf:configure/service/vprn[service-name=%s]/bgp/group' %vrtr_name)


                for ip in vrouter_bgp_neighbor:
                    vrtr_pair.extend([ip, vrouter_bgp_neighbor[ip]["group"].data])

                    if "peer-as" in vrouter_bgp_neighbor[ip]:
                        vrtr_pair.append(vrouter_bgp_neighbor[ip]["peer-as"].data)
                    elif "peer-as" in vrouter_bgp_group[(vrouter_bgp_neighbor[ip]["group"].data)]:
                        vrtr_pair.append(vrouter_bgp_group[(vrouter_bgp_neighbor[ip]["group"].data)]["peer-as"].data)
                    else:
                        vrtr_pair.append("None")

                for ip in vrouter_bgp_neighbor:
                    vrouter_bgp_neig_state = conn_obj.running.get('/nokia-state:state/service/vprn[service-name=%s]/bgp/neighbor[ip-address=%s]/statistics/session-state' %(vrtr_name, ip))
                    vrtr_pair.append(vrouter_bgp_neig_state)

                rows.append(vrtr_pair)


        elif vrouter_type == "router":
            for vrtr_name in vrouter_config:
                vrtr_pair = [vrtr_name, vrouter_type]
                vrouter_bgp_neighbor = conn_obj.running.get('/nokia-conf:configure/router[router-name="Base"]/bgp/neighbor')
                vrouter_bgp_group = conn_obj.running.get('/nokia-conf:configure/router[router-name="Base"]/bgp/group')

                for ip in vrouter_bgp_neighbor:
                    vrtr_pair.extend([ip, vrouter_bgp_neighbor[ip]["group"].data])

                    if "peer-as" in vrouter_bgp_neighbor[ip]:
                        vrtr_pair.append(vrouter_bgp_neighbor[ip]["peer-as"].data)
                    elif "peer-as" in vrouter_bgp_group[(vrouter_bgp_neighbor[ip]["group"].data)]:
                        vrtr_pair.append(vrouter_bgp_group[(vrouter_bgp_neighbor[ip]["group"].data)]["peer-as"].data)
                    else:
                        vrtr_pair.append("None")

                for ip in vrouter_bgp_neighbor:
                    vrouter_bgp_neig_state = conn_obj.running.get('/nokia-state:state/router[router-name="Base"]/bgp/neighbor[ip-address=%s]/statistics/session-state' %ip)
                    vrtr_pair.append(vrouter_bgp_neig_state)

                rows.append(vrtr_pair)


    print_table(rows, cols)
    conn_obj.disconnect()


if __name__ == "__main__":
    get_vprn_base_bgp()
