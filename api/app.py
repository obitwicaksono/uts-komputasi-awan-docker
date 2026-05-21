from flask import Flask, request, jsonify
import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)


def get_db_connection(retries=10, delay=2):
	for attempt in range(1, retries + 1):
		try:
			return psycopg2.connect(
				host=os.getenv("DB_HOST", "db"),
				database=os.getenv("DB_NAME", "barangdb"),
				user=os.getenv("DB_USER", "postgres"),
				password=os.getenv("DB_PASSWORD", "pass123"),
			)
		except psycopg2.OperationalError:
			if attempt == retries:
				raise
			time.sleep(delay)


def init_db():
	conn = get_db_connection()
	with conn:
		with conn.cursor() as cur:
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS barang (
					id SERIAL PRIMARY KEY,
					nama VARCHAR(100) NOT NULL,
					harga INT NOT NULL
				);
				"""
			)
	conn.close()


@app.route("/barang", methods=["GET"])
def list_barang():
	conn = get_db_connection()
	with conn:
		with conn.cursor(cursor_factory=RealDictCursor) as cur:
			cur.execute("SELECT id, nama, harga FROM barang ORDER BY id")
			rows = cur.fetchall()
	conn.close()
	return jsonify(rows)


@app.route("/barang", methods=["POST"])
def add_barang():
	payload = request.get_json(force=True)
	nama = payload.get("nama")
	harga = payload.get("harga")

	if not nama or harga is None:
		return jsonify({"error": "fields nama and harga are required"}), 400

	conn = get_db_connection()
	with conn:
		with conn.cursor(cursor_factory=RealDictCursor) as cur:
			cur.execute(
				"INSERT INTO barang (nama, harga) VALUES (%s, %s) RETURNING id, nama, harga",
				(nama, harga),
			)
			item = cur.fetchone()
	conn.close()
	return jsonify(item), 201


if __name__ == "__main__":
	init_db()
	app.run(host="0.0.0.0", port=8080)