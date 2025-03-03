function loadConfig(configPath) {
    try {
        const fileContent = fs.readFileSync(configPath, 'utf8');
        const config = yaml.load(fileContent);
        return config;
    } catch (error) {
        console.error(`Error loading configuration file: ${error.message}`);
        throw error;
    }
}
(async () => {
    const configPath = '../config.yaml';

    if (!fs.existsSync(configPath)) {
        throw new Error(`Config file not found: ${configPath}`);
    }

    const config = loadConfig(configPath);
    const BASE_DIR = config.BASE_DIR || 'Not specified';
//    const DB_PATN = config.DB_DIR || 'Not specified';


// Resolve relative path to absolute path
const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(bodyParser.json());

app.post('/resolve_path/', (req, res) => {
    try {
        console.log('Request body:', req.body);

        const { user_id, relative_path, timestamp } = req.body;

        if (!user_id || !relative_path) {
            return res.status(400).json({ error: "Missing required fields: 'user_id' or 'relative_path'." });
        }

        console.log('Resolving absolute path...');
        const absolutePath = resolveAbsolutePath(relative_path);
        console.log('Resolved absolute path:', absolutePath);

        if (!absolutePath.startsWith(BASE_DIR)) {
            return res.status(403).json({ error: "Invalid path. Path is outside allowed base directory." });
        }

        console.log('Saving folder path...');
        saveFolderPath({
            user_id,
            folder_path: absolutePath,
            timestamp
        });

        res.status(200).json({ absolute_path: absolutePath });
    } catch (error) {
        console.error('Error resolving path:', error);
        res.status(500).json({ error: "Internal server error." });
    }
});

// Resolve relative path to absolute path
function resolveAbsolutePath(relativePath) {
    return path.resolve(BASE_DIR, relativePath); // 拼接绝对路径
}

// Save folder path to database
function saveFolderPath(data) {
//    const DB_PATH = path.join(__dirname, '../db/user.json');
    const DB_PATH = path.join(__dirname, DB_PATH);
    try {
        // Ensure directory exists
        const dbDir = path.dirname(DB_PATH);
        if (!fs.existsSync(dbDir)) {
            fs.mkdirSync(dbDir, { recursive: true });
        }

        // Load existing data
        let existingData = [];
        if (fs.existsSync(DB_PATH)) {
            const jsonData = fs.readFileSync(DB_PATH, 'utf-8');
            existingData = JSON.parse(jsonData) || [];
        }

        // Update or add data
        const userEntry = existingData.find(entry => entry.user_id === data.user_id);
        if (userEntry) {
            userEntry.folder_path = data.folder_path; // 更新为绝对路径
            userEntry.timestamp = data.timestamp;
        } else {
            existingData.push(data);
        }

        // Write updated data
        fs.writeFileSync(DB_PATH, JSON.stringify(existingData, null, 4), 'utf-8');
        console.log(`Folder path saved successfully.`);
    } catch (error) {
        console.error('Error saving folder path:', error);
    }
}

// Handle chat request
app.post('/chat_kb/', (req, res) => {
    const { question, user_id, pdf_directory, timestamp } = req.body;

    if (!question || !user_id || !pdf_directory || !timestamp) {
        return res.status(400).json({ error: "Missing required fields." });
    }

    try {
        const response = handleChatRequest(question, user_id, pdf_directory, timestamp);
        res.status(200).json(response);
    } catch (error) {
        console.error('Error handling chat request:', error);
        res.status(500).json({ error: "Internal server error." });
    }
});

// Handle chat request logic
function handleChatRequest(question, user_id, pdfDirectory, timestamp) {
    try {
        const response = `You asked: "${question}". Your PDF directory is "${pdfDirectory}". Timestamp: ${timestamp}`;
        return { response };
    } catch (error) {
        console.error('Error handling chat request:', error);
        return { response: 'Error processing your request.' };
    }
}

// Start the server
const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Backend server is running on http://localhost:${PORT}`);
});
