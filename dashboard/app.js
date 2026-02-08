// Culture color mapping (matches Python visualization)
const CULTURE_COLORS = {
    'Japanese': '#1f77b4',
    'American': '#ff7f0e',
    'German': '#2ca02c',
    'Australian': '#d62728',
    'French': '#9467bd',
    'British': '#8c564b'
};

// Global data storage
let paintingsData = [];
let annotationsData = {};

/**
 * Load JSON data files
 */
async function loadData() {
    try {
        const [paintingsRes, annotationsRes] = await Promise.all([
            fetch('data/paintings.json'),
            fetch('data/cluster_annotations.json')
        ]);

        if (!paintingsRes.ok || !annotationsRes.ok) {
            throw new Error('Failed to load data files');
        }

        const paintings = await paintingsRes.json();
        const annotations = await annotationsRes.json();

        return { paintings, annotations };
    } catch (error) {
        console.error('Error loading data:', error);
        alert('Failed to load dashboard data. Please ensure data files are present in the data/ directory.');
        throw error;
    }
}

/**
 * Create Plotly scatter plot
 */
function createPlot(paintings, annotations) {
    // Group paintings by culture
    const traces = [];
    const cultures = Object.keys(CULTURE_COLORS);

    cultures.forEach(culture => {
        const culturePaintings = paintings.filter(p => p.artist_culture === culture);

        if (culturePaintings.length === 0) return;

        const trace = {
            x: culturePaintings.map(p => p.plot_x),
            y: culturePaintings.map(p => p.plot_y),
            mode: 'markers',
            type: 'scatter',
            name: culture,
            customdata: culturePaintings.map(p => p.id),
            hovertemplate: '<b>%{text}</b><br>Object: %{customdata[1]}<extra></extra>',
            text: culturePaintings.map(p => p.title),
            customdata: culturePaintings.map(p => [p.id, p.dominant_blue_object]),
            marker: {
                size: 10,
                color: CULTURE_COLORS[culture],
                opacity: 0.7,
                line: {
                    color: 'white',
                    width: 1
                }
            }
        };

        traces.push(trace);
    });

    // Create annotation objects for top clusters
    const plotAnnotations = annotations.top_clusters.map(cluster => ({
        x: cluster.centroid_x,
        y: cluster.centroid_y,
        text: `<b>${cluster.object_type}</b><br>(n=${cluster.count})`,
        showarrow: false,
        font: {
            size: 11,
            color: '#333',
            family: 'Arial, sans-serif'
        },
        bgcolor: 'rgba(255, 255, 255, 0.9)',
        bordercolor: '#666',
        borderwidth: 1,
        borderpad: 4,
        xanchor: 'center',
        yanchor: 'middle'
    }));

    // Layout configuration
    const layout = {
        showlegend: true,
        legend: {
            x: 1,
            y: 1,
            xanchor: 'right',
            yanchor: 'top',
            bgcolor: 'rgba(255, 255, 255, 0.9)',
            bordercolor: '#e0e0e0',
            borderwidth: 1
        },
        xaxis: {
            showticklabels: false,
            showgrid: true,
            gridcolor: '#e0e0e0',
            zeroline: false,
            title: ''
        },
        yaxis: {
            showticklabels: false,
            showgrid: true,
            gridcolor: '#e0e0e0',
            zeroline: false,
            title: ''
        },
        hovermode: 'closest',
        annotations: plotAnnotations,
        plot_bgcolor: '#fafafa',
        paper_bgcolor: '#fff',
        margin: { l: 40, r: 40, t: 40, b: 40 }
    };

    // Config
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };

    // Create plot
    Plotly.newPlot('plot', traces, layout, config);
}

/**
 * Attach click handler to plot
 */
function attachClickHandler(paintings) {
    const plotDiv = document.getElementById('plot');

    plotDiv.on('plotly_click', function(data) {
        if (data.points.length > 0) {
            const point = data.points[0];
            const paintingId = point.customdata[0];

            // Find painting object
            const painting = paintings.find(p => p.id === paintingId);

            if (painting) {
                showPaintingDetail(painting);
            }
        }
    });
}

/**
 * Show painting detail in right panel
 */
function showPaintingDetail(painting) {
    // Hide welcome screen, show detail view
    document.getElementById('welcome-screen').style.display = 'none';
    document.getElementById('detail-view').style.display = 'block';

    // Populate fields
    document.getElementById('detail-title').textContent = painting.title || 'Untitled';
    document.getElementById('detail-artist').textContent = painting.artist_name || 'Unknown';
    document.getElementById('detail-culture').textContent = painting.artist_culture || 'Unknown';
    document.getElementById('detail-date').textContent = painting.dated || 'Unknown';
    document.getElementById('detail-classification').textContent = painting.classification || 'Unknown';
    document.getElementById('detail-object').textContent = painting.dominant_blue_object || 'N/A';
    document.getElementById('detail-id').textContent = painting.id;

    // Color information
    const rgbText = `RGB: (${painting.blue_rgb[0]}, ${painting.blue_rgb[1]}, ${painting.blue_rgb[2]})`;
    document.getElementById('detail-color-rgb').textContent = rgbText;
    document.getElementById('detail-color-hex').textContent = painting.blue_hex;
    document.getElementById('detail-color-swatch').style.backgroundColor = painting.blue_hex;

    // Coverage and confidence
    const coveragePercent = (painting.coverage_percent * 100).toFixed(2);
    document.getElementById('detail-coverage').textContent = `${coveragePercent}%`;
    document.getElementById('detail-confidence').textContent = painting.confidence || 'medium';

    // Reasoning
    document.getElementById('detail-reasoning').textContent = painting.reasoning || 'N/A';

    // Load image
    const img = document.getElementById('detail-image');
    const imgError = document.getElementById('image-error');

    img.style.display = 'block';
    imgError.style.display = 'none';

    img.src = `images/${painting.image_name}`;

    img.onerror = () => {
        img.style.display = 'none';
        imgError.style.display = 'block';
    };

    // Scroll to top of detail panel
    document.querySelector('.detail-panel').scrollTop = 0;
}

/**
 * Close detail view
 */
function closeDetailView() {
    document.getElementById('detail-view').style.display = 'none';
    document.getElementById('welcome-screen').style.display = 'block';
}

/**
 * Initialize dashboard
 */
async function init() {
    try {
        console.log('Loading data...');
        const { paintings, annotations } = await loadData();

        console.log(`Loaded ${paintings.length} paintings`);
        console.log(`Loaded ${annotations.top_clusters.length} cluster annotations`);

        // Store globally
        paintingsData = paintings;
        annotationsData = annotations;

        console.log('Creating plot...');
        createPlot(paintings, annotations);

        console.log('Attaching click handler...');
        attachClickHandler(paintings);

        // Attach close button handler
        document.getElementById('close-detail').addEventListener('click', closeDetailView);

        console.log('Dashboard initialized successfully');
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        document.getElementById('plot').innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #999;">
                <h3>Failed to load dashboard</h3>
                <p>Please check the console for error details.</p>
            </div>
        `;
    }
}

// Start initialization when page loads
window.addEventListener('DOMContentLoaded', init);
