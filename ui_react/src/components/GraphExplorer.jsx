import React, { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Loader2, RefreshCw, ZoomIn, ZoomOut, Maximize, AlertCircle } from 'lucide-react';
import axios from 'axios';

const GraphExplorer = () => {
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [limit, setLimit] = useState(100);
    const graphRef = useRef();

    const fetchGraphData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`http://localhost:8000/graph/data?limit=${limit}`);
            setGraphData(response.data);
        } catch (err) {
            console.error("Failed to fetch graph data:", err);
            setError("Failed to load graph data. Please ensure the backend is running.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchGraphData();
    }, [limit]);

    const handleRefresh = () => {
        fetchGraphData();
    };

    const handleZoomIn = () => {
        graphRef.current?.zoom(graphRef.current.zoom() * 1.2, 400);
    };

    const handleZoomOut = () => {
        graphRef.current?.zoom(graphRef.current.zoom() / 1.2, 400);
    };

    const handleZoomToFit = () => {
        graphRef.current?.zoomToFit(400, 50);
    };

    return (
        <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">Graph Explorer</h2>
                    <p className="text-sm text-slate-500">Visualize entities and relationships in FalkorDB</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <label className="text-sm text-slate-600 font-medium">Limit:</label>
                        <select
                            value={limit}
                            onChange={(e) => setLimit(Number(e.target.value))}
                            className="text-sm border border-slate-300 rounded-md px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value={50}>50</option>
                            <option value={100}>100</option>
                            <option value={200}>200</option>
                            <option value={500}>500</option>
                        </select>
                    </div>
                    <button
                        onClick={handleRefresh}
                        className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                        title="Refresh Graph"
                    >
                        <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
                    </button>
                </div>
            </div>

            <div className="flex-1 bg-slate-900 rounded-xl overflow-hidden shadow-lg border border-slate-700 relative">
                {loading && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm">
                        <div className="flex flex-col items-center gap-3 text-blue-400">
                            <Loader2 size={32} className="animate-spin" />
                            <span className="font-medium">Loading Graph Data...</span>
                        </div>
                    </div>
                )}

                {error && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm">
                        <div className="bg-red-900/20 border border-red-800 p-6 rounded-xl flex flex-col items-center gap-3 text-red-400 max-w-md text-center">
                            <AlertCircle size={32} />
                            <span className="font-medium">{error}</span>
                            <button
                                onClick={fetchGraphData}
                                className="px-4 py-2 bg-red-800/50 hover:bg-red-800 text-white rounded-lg text-sm transition-colors"
                            >
                                Retry
                            </button>
                        </div>
                    </div>
                )}

                {!loading && !error && graphData.nodes.length === 0 && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center text-slate-500">
                        <div className="text-center">
                            <p className="text-lg font-medium mb-2">No Data Found</p>
                            <p className="text-sm">Try adding documents or increasing the limit.</p>
                        </div>
                    </div>
                )}

                <ForceGraph2D
                    ref={graphRef}
                    graphData={graphData}
                    nodeLabel="name"
                    nodeColor={node => node.label === 'Document' ? '#3b82f6' : '#a855f7'}
                    nodeRelSize={6}
                    linkColor={() => '#475569'}
                    linkDirectionalArrowLength={3.5}
                    linkDirectionalArrowRelPos={1}
                    backgroundColor="#0f172a"

                    // Custom Node Rendering with Text
                    nodeCanvasObject={(node, ctx, globalScale) => {
                        const label = node.name;
                        const fontSize = 12 / globalScale;
                        ctx.font = `${fontSize}px Sans-Serif`;
                        const textWidth = ctx.measureText(label).width;
                        const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); // some padding

                        // Draw Node Circle
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
                        ctx.fillStyle = node.label === 'Document' ? '#3b82f6' : '#a855f7';
                        ctx.fill();

                        // Draw Text Label
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                        ctx.fillText(label, node.x, node.y + 8);

                        node.__bckgDimensions = bckgDimensions; // to re-use in nodePointerAreaPaint
                    }}
                    nodePointerAreaPaint={(node, color, ctx) => {
                        ctx.fillStyle = color;
                        const bckgDimensions = node.__bckgDimensions;
                        bckgDimensions && ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);
                    }}

                    // Custom Link Rendering with Text
                    linkCanvasObject={(link, ctx, globalScale) => {
                        const start = link.source;
                        const end = link.target;

                        // Draw Line
                        ctx.beginPath();
                        ctx.moveTo(start.x, start.y);
                        ctx.lineTo(end.x, end.y);
                        ctx.strokeStyle = '#475569';
                        ctx.lineWidth = 1 / globalScale;
                        ctx.stroke();

                        // Draw Label
                        if (link.type) {
                            const textPos = Object.assign(...['x', 'y'].map(c => ({
                                [c]: start[c] + (end[c] - start[c]) / 2 // calc middle point
                            })));

                            const relLabel = link.type;
                            const fontSize = 10 / globalScale;
                            ctx.font = `${fontSize}px Sans-Serif`;

                            // Draw background for text to make it readable
                            const textWidth = ctx.measureText(relLabel).width;
                            ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
                            ctx.fillRect(textPos.x - textWidth / 2 - 2, textPos.y - fontSize / 2 - 2, textWidth + 4, fontSize + 4);

                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillStyle = '#94a3b8';
                            ctx.fillText(relLabel, textPos.x, textPos.y);
                        }
                    }}
                    linkCanvasObjectMode={() => 'after'} // Draw on top of line

                    onNodeClick={node => {
                        // Center view on node
                        graphRef.current?.centerAt(node.x, node.y, 1000);
                        graphRef.current?.zoom(4, 2000);
                    }}
                    cooldownTicks={100}
                    onEngineStop={() => graphRef.current?.zoomToFit(400)}
                />

                {/* Controls Overlay */}
                <div className="absolute bottom-4 right-4 flex flex-col gap-2 bg-slate-800/90 p-2 rounded-lg border border-slate-700 backdrop-blur-sm">
                    <button onClick={handleZoomIn} className="p-2 text-slate-300 hover:text-white hover:bg-slate-700 rounded-md transition-colors" title="Zoom In">
                        <ZoomIn size={20} />
                    </button>
                    <button onClick={handleZoomOut} className="p-2 text-slate-300 hover:text-white hover:bg-slate-700 rounded-md transition-colors" title="Zoom Out">
                        <ZoomOut size={20} />
                    </button>
                    <button onClick={handleZoomToFit} className="p-2 text-slate-300 hover:text-white hover:bg-slate-700 rounded-md transition-colors" title="Fit to Screen">
                        <Maximize size={20} />
                    </button>
                </div>

                {/* Legend */}
                <div className="absolute top-4 left-4 bg-slate-800/90 p-3 rounded-lg border border-slate-700 backdrop-blur-sm">
                    <div className="flex flex-col gap-2 text-xs font-medium text-slate-300">
                        <div className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                            <span>Entity</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                            <span>Document</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GraphExplorer;
