import fs from 'fs'
import { fetchStocksData } from './utils/api.js'
import { writeToTopic } from './utils/kafka.js'

const dev = process.env.DEV
const filePath = './data.json'

// Transform 
function prepData(data) {
  const metaData = data['Meta Data'];
  const timeSeriesData = data['Time Series (5min)'];
  const convertedData = [];


  for (const [timestamp, values] of Object.entries(timeSeriesData)) {
    convertedData.push({
      timestamp,
      stock: metaData['2. Symbol'],
      open: parseFloat(values['1. open']),
      high: parseFloat(values['2. high']),
      low: parseFloat(values['3. low']),
      close: parseFloat(values['4. close']),
      volume: parseInt(values['5. volume'], 10)
    });
  }

  convertedData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  return {
    metaData,
    timeSeries: convertedData
  };
}

export async function main() {
  if (fs.existsSync(filePath) && dev) {
    console.log('data.json file already exists simulating events');

    const rawData = fs.readFileSync(filePath, 'utf8')
    const jsonData = JSON.parse(rawData)
    await writeToTopic(jsonData.timeSeries, 'stocks_topic')
  }
  else {
    const res = await fetchStocksData()
    const data = prepData(res)

    console.log('successfully fetch data, writing to data.json');
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');

    await writeToTopic(data.timeSeries, 'stocks_topic')
    console.log('***** DONE *****');
  }
}
