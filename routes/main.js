const express = require('express');
const axios = require('axios');
const router = express.Router();
// Fetch JSON data from FastAPI
router.get('/get_data', async (req, res) => {
    try {
        const response = await axios.get('http://192.168.1.105:3000/get_data');
        res.json(response.data);
    } catch (error) {
        console.error('Error fetching data:', error);
        res.status(500).json({ message: "Failed to fetch data" });
    }
});

// Serve first graph image
router.get('/get_first_graph/:region/:start_year/:end_year/:select_year', async (req, res) => {
    const { region, start_year, end_year, select_year } = req.params;
    try {
        const imageUrl = `http://192.168.1.105:3000/visual/region_graph/${region}/${start_year}_${end_year}/${select_year}`;
        const response = await axios.get(imageUrl, { responseType: 'arraybuffer' });
        res.writeHead(200, {
            'Content-Type': 'image/png',
            'Content-Length': response.data.length
        });
        res.end(response.data);
    } catch (error) {
        console.error('Error fetching image:', error);
        res.status(500).send('Error loading image');
    }
});

// Serve second graph image
router.get('/get_second_graph/:region1/:region2/:startYear/:endYear', async (req, res) => {
    const { region1, region2, startYear, endYear } = req.params;
    try {
        const imageUrl = `http://192.168.1.105:3000/visual/${region1}vs${region2}/${startYear}to${endYear}`;
        const response = await axios.get(imageUrl, { responseType: 'arraybuffer' });
        res.writeHead(200, {
            'Content-Type': 'image/png',
            'Content-Length': response.data.length
        });
        res.end(response.data);
    } catch (error) {
        console.error('Error fetching image:', error);
        res.status(500).send('Error loading image');
    }
});

router.get('/get_social_mobility/:region1/:region2/:startYear/:endYear', async (req, res) => {
    const { region1, region2, startYear, endYear } = req.params;
    const imageUrl = `http://192.168.1.105:3000/visual/social_graph/${startYear}_${endYear}/${region1}vs${region2}`;
    
    try {
        const response = await axios.get(imageUrl, { responseType: 'arraybuffer' });
        res.writeHead(200, {
            'Content-Type': 'image/png',
            'Content-Length': response.data.length
        });
        res.end(response.data);
    } catch (error) {
        console.error('Error fetching image:', error);
        res.status(500).send('Error loading image');
    }
});

module.exports = router;