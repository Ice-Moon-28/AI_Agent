// 切换到 backend_gpt 数据库（如果不存在，会自动创建）
db = db.getSiblingDB("backend_gpt");

// 创建 `document` 集合（MongoDB 自动创建）
db.createCollection("document");

// 确保集合存在后，插入示例数据
db.document.insertMany([
    { "title": "Hello GPT", "content": "This is a test document.", "author": "User" },
    { "title": "MongoDB Setup", "content": "This script initializes the database.", "author": "Admin" }
]);

console.log("✅ Database `backend_gpt` and collection `document` successfully created.");