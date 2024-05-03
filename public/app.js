const express = require('express');
const morgan = require('morgan');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const path = require('path');
const app = express();
app.use(express.static(path.join(__dirname)));
// 디렉토리 경로 확인
console.log(path.join(__dirname));


app.set('port', process.env.PORT || 8000);

// Middleware for logging, parsing, and cookie handling
app.use(morgan('dev'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(cookieParser());

const mainRoutes = require('../routes/main');  
app.use('/', mainRoutes);

// Serve the title_page.html at the root URL
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname,'html', 'title_page.html'));
});

app.get('/first_page', (req,res) => {
    res.sendFile(path.join(__dirname,'html', 'first_page.html'));
})

app.get('/insight_page', (req,res) => {
    res.sendFile(path.join(__dirname,'html', 'social_vs.html'));
})

app.get('/draw_graph', (req,res) => {
    res.sendFile(path.join(__dirname,'html', 'draw_graph.html'));
})


// Start the server
app.listen(app.get('port'), () => {
    console.log(`Server running on port ${app.get('port')}`);
});

module.exports = app;
