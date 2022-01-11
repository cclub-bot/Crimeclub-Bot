from datetime import datetime

import pymysql


class Reporter:

    @staticmethod
    def report(module, action, text, profit=None):
        log_string = f"[{module}] -> {action} -> {text} -> {profit}"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("log.txt", "a") as f:
            f.write(f"{ts} - {log_string}\n")
        print(log_string)
        # Reporter.report_mysql(module, action, text)

    @staticmethod
    def report_mysql(module, action, text, severity=""):
        return
        try:
            con = pymysql.connect(
                host="xxx",
                user="xxx",
                password="xxx",
                database="xxx"
            )
            modstr = f"{module}->{action}"
            cur = con.cursor()
            cur.execute(
                'INSERT INTO ccb (module, severity, text, added) VALUES (%s, %s, %s, NOW())',
                (modstr, severity, text)
            )
            con.commit()
            cur.close()
            con.close()
        except Exception as e:
            print(str(e))

    @staticmethod
    def report_pool(pool):
        return
        try:
            con = pymysql.connect(
                host="xxx",
                user="xxx",
                password="xxx",
                database="xxx"
            )
            cur = con.cursor()
            for x in pool:
                cur.execute(
                    'INSERT INTO ccbv (key_data, value_data) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value_data = VALUES(value_data)',
                    (x, pool[x])
                )
            con.commit()
            cur.close()
            con.close()
        except Exception as e:
            print(str(e))
