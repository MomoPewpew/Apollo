CREATE TABLE IF NOT EXISTS prompts (
    promptID integer PRIMARY_KEY,
    promptType string,
    promptString string,
    userID integer,
    promptTags string,
    timeStamp text DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    userID integer PRIMARY_KEY,
    promptTagsActive string,
    promptTagsInactive string
);