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
let clusterAnnotations = [];  // Plotly annotation objects
let labelsVisible = true;
let selectedPaintingId = null;

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
            text: culturePaintings.map(p => p.dominant_blue_object),
            customdata: culturePaintings.map(p => [p.id, p.dominant_blue_object]),
            hovertemplate: '<b>%{text}</b><extra></extra>',
            marker: {
                size: 10,
                color: CULTURE_COLORS[culture],
                opacity: 0.7,
                line: {
                    color: culturePaintings.map(() => 'white'),
                    width: culturePaintings.map(() => 1)
                }
            }
        };

        traces.push(trace);
    });

    // Create annotation objects for top clusters
    clusterAnnotations = annotations.top_clusters.map(cluster => ({
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
        annotations: clusterAnnotations,
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
 * Toggle cluster labels visibility
 */
function toggleClusterLabels() {
    labelsVisible = !labelsVisible;
    const plotDiv = document.getElementById('plot');
    const btn = document.getElementById('toggle-labels');

    const newAnnotations = labelsVisible ? clusterAnnotations : [];
    Plotly.relayout(plotDiv, { annotations: newAnnotations });

    btn.classList.toggle('active', labelsVisible);
}

/**
 * Highlight selected point with black border, reset others
 */
function highlightSelectedPoint(paintingId) {
    const plotDiv = document.getElementById('plot');
    const traces = plotDiv.data;
    const update = { 'marker.line.color': [], 'marker.line.width': [] };

    for (let i = 0; i < traces.length; i++) {
        const ids = traces[i].customdata.map(d => d[0]);
        const lineColors = ids.map(id => id === paintingId ? '#000' : 'white');
        const lineWidths = ids.map(id => id === paintingId ? 3 : 1);

        update['marker.line.color'].push(lineColors);
        update['marker.line.width'].push(lineWidths);
    }

    // Restyle all traces
    const traceIndices = traces.map((_, i) => i);
    for (let i = 0; i < traces.length; i++) {
        Plotly.restyle(plotDiv, {
            'marker.line.color': [update['marker.line.color'][i]],
            'marker.line.width': [update['marker.line.width'][i]]
        }, [i]);
    }
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
                selectedPaintingId = paintingId;
                highlightSelectedPoint(paintingId);
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

    // VLM Reasoning (inside collapsible)
    document.getElementById('detail-confidence').textContent = painting.confidence || 'medium';
    document.getElementById('detail-reasoning').textContent = painting.reasoning || 'N/A';

    // Collapse the reasoning dropdown by default
    document.querySelector('.vlm-reasoning-dropdown').removeAttribute('open');

    // API Color section
    const apiColor = painting.original_blue_color || '';
    document.getElementById('detail-api-swatch').style.backgroundColor = apiColor || '#ccc';
    document.getElementById('detail-api-hex').textContent = apiColor || 'N/A';
    const coveragePercent = (painting.coverage_percent * 100).toFixed(2);
    document.getElementById('detail-api-coverage').textContent = `Coverage: ${coveragePercent}%`;

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
 * Close detail view and clear selection
 */
function closeDetailView() {
    document.getElementById('detail-view').style.display = 'none';
    document.getElementById('welcome-screen').style.display = 'block';

    // Clear selection highlight
    if (selectedPaintingId !== null) {
        selectedPaintingId = null;
        highlightSelectedPoint(null);  // Reset all to white
    }
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

        // Attach toggle labels handler
        document.getElementById('toggle-labels').addEventListener('click', toggleClusterLabels);

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
