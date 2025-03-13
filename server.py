from flask import Flask, render_template
import requests as rq
import pandas as pd
import os

app = Flask(__name__)

path = "250308"
api_key = "gwvhtbcs7dujznyxg7bsmu3ypx4gv73dcxsjfsdg26rzy808zty78cbtuu1c9wer"
url_base = "https://selfserve.decipherinc.com/api/v1/surveys/selfserve/563/"
quota_url = f"{url_base}{path}/quota"

global df_marker

marker_file_path = os.path.join(os.getcwd(), "marker.xlsx")
df_marker = pd.read_excel(marker_file_path)


@app.route('/')
def index():

    quota_req = rq.get(quota_url, headers={"x-apikey": api_key})
    if quota_req.status_code != 200:
        return f"Failed to fetch quota data. Status Code: {quota_req.status_code}"

    response = quota_req.json()
    response_data = rq.get(f"{url_base}{path}/data", headers={"x-apikey": api_key})
    response_data.raise_for_status()

    quota_data = []
    for quota in response.get('sheets', []):
        for sheet in response['sheets'][quota]:
            for cell in sheet.get('cells', []):
                marker = cell.get('marker')
                quota_values = response.get('markers', {}).get(marker, {})

                limit = quota_values.get('limit', 0)
                complete = quota_values.get('complete', 0)
                needs = limit - complete if limit is not None and complete is not None else None

                quota_data.append({
                    'marker': marker,
                    'limit': limit,
                    'complete': complete,
                    'needs': needs
                })

    df_quota = pd.DataFrame(quota_data)

    
    if df_marker is None:
        return "Error: marker.xlsx file not found or not loaded!"

    df_final = df_marker.merge(df_quota, on="marker", how="left")
    df_final.insert(1, "QuotaBuckets", df_final["Quota"])
    df_final.drop(columns=["Quota", "marker"], inplace=True)

    table_html = df_final.to_html(classes='table table-striped table-bordered', index=False)

    return render_template("index.html", table=table_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
