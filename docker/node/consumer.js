import { connectToPostgres } from './utils/kafka.js'

const topic = 'stocks_topic'
const consumerGroup = 'stocks_group'
const dbTable = 'stocks'

export async function main() {
  console.log(`Reading 'Events' from ${topic} and writing it to ${dbTable} Table in PostgresDB`);
  await connectToPostgres(topic, consumerGroup, dbTable).catch(console.error);
}