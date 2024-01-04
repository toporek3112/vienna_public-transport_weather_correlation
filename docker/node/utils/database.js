import pg from 'pg';
const { Pool } = pg;

const pool = new Pool({
  user: 'postgres',
  host: 'dsi_postgres',
  database: 'tmp',
  password: 'postgres',
  port: 5432,
});

export async function writeToDbTable(data, table) {
  const client = await pool.connect();
  try {
    const query = `INSERT INTO ${table}(timestamp, stock, open, high, low, close, volume) VALUES($1, $2, $3, $4, $5, $6, $7)`;
    const values = [data.timestamp, data.stock, data.open, data.high, data.low, data.close, data.volume];

    console.log(`Writing ${JSON.stringify(data)}\n to: ${table}`);

    await client.query(query, values);
  } catch (err) {
    console.error('Database write failed:', err);
  } finally {
    client.release();
  }
}

