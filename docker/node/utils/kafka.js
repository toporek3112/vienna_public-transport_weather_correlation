import { Kafka } from 'kafkajs';
import { writeToDbTable } from './database.js'

let kafkaHost = 'localhost:9092'
if (process.env.KAFKA_HOST){
    kafkaHost = process.env.KAFKA_HOST
}

// Initialize Kafka connection
const kafka = new Kafka({
    clientId: 'stocks_app',
    brokers: [kafkaHost]
});

const admin = kafka.admin();
const producer = kafka.producer();

async function ensureTopicExists(topicName) {
    await admin.connect();
    const existingTopics = await admin.listTopics();

    console.log(existingTopics);

    if (!existingTopics.includes(topicName)) {
        await admin.createTopics({
            topics: [{ topic: topicName }],
        });
        console.log(`Topic ${topicName} created`);
    }

    await admin.disconnect();
}

export async function writeToTopic(array, topic) {
    console.log(`'Events' count: ${array.length}`);

    await ensureTopicExists(topic);
    await producer.connect();

    for (let item of array) {
        let r = Math.floor(Math.random() * 1000);
        item = JSON.stringify(item)

        console.log('Sending event:', item);

        await producer.send({
            topic,
            messages: [{ value: item }],
        });

        await new Promise(resolve => setTimeout(resolve, r));
    }

    await producer.disconnect();
}

export async function readFromTopic(topic, consumerGroup) {
    console.log(`Reading 'Events' from ${topic}`);

    const consumer = kafka.consumer({ groupId: consumerGroup });

    await consumer.connect();
    await consumer.subscribe({ topic: topic });

    await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
            console.log({
                partition,
                offset: message.offset,
                value: message.value.toString(),
            });
            // Additional message processing logic here
        },
    });
}

export async function connectToPostgres(topic, consumerGroup, table) {
    const consumer = kafka.consumer({ groupId: consumerGroup });

    await consumer.connect();
    await consumer.subscribe({ topic: topic });
    
    await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
            const data = JSON.parse(message.value.toString());
            await writeToDbTable(data, table);
        },
    });


}
