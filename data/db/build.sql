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