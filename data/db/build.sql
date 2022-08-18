CREATE TABLE IF NOT EXISTS prompts (
    promptID INTEGER PRIMARY KEY AUTOINCREMENT,
    promptType STRING,
    promptString STRING,
    userID INTEGER,
    promptTags STRING,
    timeStamp STRING DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    userID INTEGER PRIMARY KEY,
    promptTagsActive STRING DEFAULT ",",
    promptTagsInactive STRING DEFAULT ","
);

CREATE TABLE IF NOT EXISTS tasks (
    taskID INTEGER PRIMARY KEY AUTOINCREMENT,
    receiveType STRING,
    userID INTEGER,
    channelID INTEGER,
    instructions STRING,
    estimatedTime INTEGER,
    server STRING,
    timeSent STRING,
    timeReceived STRING,
    outputURL STRING
);