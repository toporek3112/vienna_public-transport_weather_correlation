import fetch from 'node-fetch';
import fs from 'fs'

const data = fs.readFileSync('config.json', 'utf8');
const config = JSON.parse(data);

const apiKey = config.apiKey;
const stock = process.env.STOCK

export async function fetchStocksData() {
  console.log(`***** Fetching data for stock: ${stock} *****`);

  try {
      const response = await fetch(`https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=${stock}&interval=5min&outputsize=full&apikey=${apiKey}`);
      const data = await response.json();
      return data
  } catch (error) {
      console.error('Error fetching data:', error);
  }
}