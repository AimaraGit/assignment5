
import psycopg2
import psycopg2.extras  

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "weather_orders",   
    "user":     "postgres",        
    "password": "12345678",       
}

def get_connection(config=None):
    
    cfg = config or DB_CONFIG
    return psycopg2.connect(**cfg)

def create_tables(config=None):
    conn = get_connection(config)
    try:
        with conn:                    
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id   SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        city VARCHAR(100) NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id         SERIAL PRIMARY KEY,
                        user_id    INTEGER NOT NULL REFERENCES users(id),
                        product    VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
    finally:
        conn.close()

def get_user(user_id: int, config=None) -> dict | None:
    conn = get_connection(config)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()

def save_order(user_id: int, product: str, config=None) -> int:
    conn = get_connection(config)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO orders (user_id, product) VALUES (%s, %s) RETURNING id",
                    (user_id, product)
                )
                order_id = cur.fetchone()[0]
                return order_id
    finally:
        conn.close()

def create_user(name: str, city: str, config=None) -> int:
    conn = get_connection(config)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (name, city) VALUES (%s, %s) RETURNING id",
                    (name, city)
                )
                return cur.fetchone()[0]
    finally:
        conn.close()

def get_orders_for_user(user_id: int, config=None) -> list:
    conn = get_connection(config)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at",
                (user_id,)
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()
    print("✅ Tables created successfully in PostgreSQL!")