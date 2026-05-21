from flask import Flask, render_template, request, redirect, url_for
import os
import requests

app = Flask(__name__)
API_URL = os.getenv("API_URL", "http://api:8080")


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        harga = request.form.get("harga", "").strip()

        if not nama or not harga:
            error = "Nama dan harga harus diisi"
        else:
            try:
                response = requests.post(
                    f"{API_URL}/barang",
                    json={"nama": nama, "harga": int(harga)},
                    timeout=5,
                )
                response.raise_for_status()
                return redirect(url_for("index"))
            except Exception as exc:
                error = f"Gagal menyimpan barang: {exc}"

    barang = []
    try:
        response = requests.get(f"{API_URL}/barang", timeout=5)
        response.raise_for_status()
        barang = response.json()
    except Exception as exc:
        if not error:
            error = f"Gagal mengambil daftar barang: {exc}"

    return render_template("index.html", barang=barang, error=error, api_url=API_URL)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
