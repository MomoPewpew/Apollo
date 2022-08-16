CREATE TABLE IF NOT EXISTS prompts (
    promptID integer PRIMARY KEY,
    promptType string,
    promptString string,
    userID integer,
    promptTags string,
    timeStamp text DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    userID integer PRIMARY KEY,
    promptTagsActive string DEFAULT ",",
    promptTagsInactive string DEFAULT ","
);