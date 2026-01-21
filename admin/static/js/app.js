// Message Types (matching Python Message.py)
const MessageType = {
    DECLARATION: 'DECLARATION',
    ENVOI: {
        TEXT: 'ENVOI_TEXT',
        IMAGE: 'ENVOI_IMAGE',
        AUDIO: 'ENVOI_AUDIO',
        VIDEO: 'ENVOI_VIDEO',
        CLIENT_LIST: 'ENVOI_CLIENT_LIST'
    },
    RECEPTION: {
        TEXT: 'RECEPTION_TEXT',
        IMAGE: 'RECEPTION_IMAGE',
        AUDIO: 'RECEPTION_AUDIO',
        VIDEO: 'RECEPTION_VIDEO',
        CLIENT_LIST: 'RECEPTION_CLIENT_LIST'
    },
    SYS_MESSAGE: 'SYS_MESSAGE',
    WARNING: 'WARNING',
    ADMIN: {
        ROUTING_LOG: 'ADMIN_ROUTING_LOG',
        CLIENT_CONNECTED: 'ADMIN_CLIENT_CONNECTED',
        CLIENT_DISCONNECTED: 'ADMIN_CLIENT_DISCONNECTED',
        CLIENT_LIST_FULL: 'ADMIN_CLIENT_LIST_FULL'
    }
};

// D3.js Network Graph Class
class NetworkGraph {
    constructor(container) {
        this.container = container;
        this.width = container.clientWidth || 600;
        this.height = container.clientHeight || 400;

        this.nodes = [
            { id: 'SERVER', type: 'server', fx: this.width / 2, fy: this.height / 2 }
        ];
        this.links = [];

        this.initSVG();
        this.initSimulation();

        // Handle resize
        window.addEventListener('resize', () => this.resize());
    }

    initSVG() {
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', [0, 0, this.width, this.height]);

        // Container groups
        this.linkGroup = this.svg.append('g').attr('class', 'links');
        this.nodeGroup = this.svg.append('g').attr('class', 'nodes');
        this.labelGroup = this.svg.append('g').attr('class', 'labels');
        this.animationGroup = this.svg.append('g').attr('class', 'animations');
    }

    initSimulation() {
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(120))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(50))
            .on('tick', () => this.ticked());
    }

    addClient(username) {
        // Check if client already exists
        if (this.nodes.find(n => n.id === username)) return;

        // Add client node with position around server
        const angle = Math.random() * 2 * Math.PI;
        const radius = 150;
        this.nodes.push({
            id: username,
            type: 'client',
            x: this.width / 2 + radius * Math.cos(angle),
            y: this.height / 2 + radius * Math.sin(angle)
        });

        // Add link to server
        this.links.push({
            source: username,
            target: 'SERVER'
        });

        this.update();
    }

    removeClient(username) {
        this.nodes = this.nodes.filter(n => n.id !== username);
        this.links = this.links.filter(l =>
            (l.source.id || l.source) !== username && (l.target.id || l.target) !== username
        );
        this.update();
    }

    setClients(usernames) {
        // Reset to just server
        this.nodes = [
            { id: 'SERVER', type: 'server', fx: this.width / 2, fy: this.height / 2 }
        ];
        this.links = [];

        // Add all clients
        const filteredUsernames = usernames.filter(u => u !== 'ADMIN' && !u.startsWith('ADMIN_'));
        filteredUsernames.forEach((username, index) => {
            const angle = (index / filteredUsernames.length) * 2 * Math.PI - Math.PI / 2;
            const radius = Math.min(this.width, this.height) * 0.35;
            this.nodes.push({
                id: username,
                type: 'client',
                x: this.width / 2 + radius * Math.cos(angle),
                y: this.height / 2 + radius * Math.sin(angle)
            });
            this.links.push({
                source: username,
                target: 'SERVER'
            });
        });

        this.update();
    }

    update() {
        // Update links
        const link = this.linkGroup.selectAll('line')
            .data(this.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`);

        link.exit().remove();

        link.enter().append('line')
            .attr('stroke', 'rgba(255, 255, 255, 0.08)')
            .attr('stroke-width', 2)
            .merge(link);

        // Update nodes
        const node = this.nodeGroup.selectAll('circle')
            .data(this.nodes, d => d.id);

        node.exit().remove();

        node.enter().append('circle')
            .attr('r', d => d.type === 'server' ? 35 : 25)
            .attr('fill', d => d.type === 'server' ? '#1a1a24' : 'rgba(40, 40, 55, 0.9)')
            .attr('stroke', d => d.type === 'server' ? '#00f5d4' : '#7b2ff7')
            .attr('stroke-width', d => d.type === 'server' ? 3 : 2)
            .call(this.drag())
            .merge(node);

        // Update labels
        const label = this.labelGroup.selectAll('text')
            .data(this.nodes, d => d.id);

        label.exit().remove();

        label.enter().append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', d => d.type === 'server' ? 5 : 5)
            .attr('fill', '#ffffff')
            .attr('font-size', d => d.type === 'server' ? '14px' : '11px')
            .attr('font-weight', '600')
            .attr('letter-spacing', '1px')
            .text(d => d.type === 'server' ? 'S' : d.id.substring(0, 3))
            .merge(label);

        // Restart simulation
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        this.simulation.alpha(0.3).restart();
    }

    ticked() {
        this.linkGroup.selectAll('line')
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        this.nodeGroup.selectAll('circle')
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);

        this.labelGroup.selectAll('text')
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }

    animateMessage(from, to) {
        const sourceNode = this.nodes.find(n => n.id === from);
        const serverNode = this.nodes.find(n => n.id === 'SERVER');

        if (!sourceNode || !serverNode) return;

        // Create animated circle: source -> server
        const particle1 = this.animationGroup.append('circle')
            .attr('r', 8)
            .attr('fill', '#00f5d4')
            .attr('cx', sourceNode.x)
            .attr('cy', sourceNode.y);

        particle1.transition()
            .duration(400)
            .attr('cx', serverNode.x)
            .attr('cy', serverNode.y)
            .on('end', () => {
                particle1.remove();

                // Server -> target(s)
                if (to === 'ALL') {
                    // Broadcast: animate to all clients
                    this.nodes.filter(n => n.type === 'client').forEach(target => {
                        this.animateToTarget(serverNode, target);
                    });
                } else {
                    const targetNode = this.nodes.find(n => n.id === to);
                    if (targetNode) {
                        this.animateToTarget(serverNode, targetNode);
                    }
                }
            });
    }

    animateToTarget(from, to) {
        const particle = this.animationGroup.append('circle')
            .attr('r', 8)
            .attr('fill', '#f72585')
            .attr('cx', from.x)
            .attr('cy', from.y);

        particle.transition()
            .duration(400)
            .attr('cx', to.x)
            .attr('cy', to.y)
            .on('end', () => particle.remove());
    }

    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                if (d.type !== 'server') {
                    d.fx = null;
                    d.fy = null;
                }
            });
    }

    resize() {
        this.width = this.container.clientWidth || 600;
        this.height = this.container.clientHeight || 400;
        this.svg.attr('viewBox', [0, 0, this.width, this.height]);

        // Re-center server
        const server = this.nodes.find(n => n.id === 'SERVER');
        if (server) {
            server.fx = this.width / 2;
            server.fy = this.height / 2;
        }

        this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
        this.simulation.alpha(0.3).restart();
    }
}

// Admin client class
class AdminClient {
    constructor(wsUrl) {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.username = 'ADMIN';
        this.clients = []; // Array of {username, connected_at, last_activity, status}
        this.isConnected = false;
        this.communicationLogs = [];

        this.initElements();
        this.initEventListeners();
        this.initNetworkGraph();
    }

    initElements() {
        // Status elements
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');

        // Client cards
        this.clientCards = document.getElementById('clientCards');
        this.clientCount = document.getElementById('clientCount');

        // Communication log
        this.communicationLog = document.getElementById('communicationLog');

        // Network graph container
        this.networkGraphContainer = document.getElementById('networkGraph');

        // Control buttons
        this.connectBtn = document.getElementById('connectBtn');
        this.disconnectBtn = document.getElementById('disconnectBtn');
        this.clearLogBtn = document.getElementById('clearLog');
    }

    initEventListeners() {
        this.connectBtn.addEventListener('click', () => this.connect());
        this.disconnectBtn.addEventListener('click', () => this.disconnect());
        this.clearLogBtn.addEventListener('click', () => this.clearLog());
    }

    initNetworkGraph() {
        // Wait for container to be visible
        setTimeout(() => {
            this.networkGraph = new NetworkGraph(this.networkGraphContainer);
        }, 100);
    }

    connect() {
        if (this.ws) {
            this.ws.close();
        }

        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => this.onOpen();
            this.ws.onclose = () => this.onClose();
            this.ws.onerror = (error) => this.onError(error);
            this.ws.onmessage = (event) => this.onMessage(event);
        } catch (error) {
            console.error('Connection error:', error);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }

    onOpen() {
        this.isConnected = true;
        this.updateConnectionStatus(true);

        // Send declaration as ADMIN
        this.send({
            message_type: MessageType.DECLARATION,
            data: {
                emitter: this.username,
                receiver: 'SERVER',
                value: this.username
            }
        });

        // Request client list
        this.send({
            message_type: MessageType.ENVOI.CLIENT_LIST,
            data: {
                emitter: this.username,
                receiver: 'SERVER',
                value: ''
            }
        });
    }

    onClose() {
        this.isConnected = false;
        this.updateConnectionStatus(false);
        this.clients = [];
        this.updateClientCards();
        if (this.networkGraph) {
            this.networkGraph.setClients([]);
        }
    }

    onError(error) {
        console.error('WebSocket error:', error);
    }

    onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }

    handleMessage(message) {
        const type = message.message_type;
        const data = message.data;

        switch (type) {
            // Admin-specific messages
            case MessageType.ADMIN.ROUTING_LOG:
                this.handleRoutingLog(data);
                break;

            case MessageType.ADMIN.CLIENT_CONNECTED:
                this.handleClientConnected(data);
                break;

            case MessageType.ADMIN.CLIENT_DISCONNECTED:
                this.handleClientDisconnected(data);
                break;

            case MessageType.ADMIN.CLIENT_LIST_FULL:
                this.handleFullClientList(data);
                break;

            // Standard messages (fallback)
            case MessageType.RECEPTION.CLIENT_LIST:
                this.handleClientList(data);
                break;

            case MessageType.SYS_MESSAGE:
                // Handle ping
                if (data.value === 'ping') {
                    this.send({
                        message_type: MessageType.SYS_MESSAGE,
                        data: {
                            emitter: this.username,
                            receiver: '',
                            value: 'pong'
                        }
                    });
                }
                break;

            default:
                // Ignore other message types
                break;
        }
    }

    handleRoutingLog(data) {
        // Add to communication log (no content, just routing info)
        const logEntry = {
            timestamp: new Date(data.value.timestamp),
            emitter: data.value.emitter,
            receiver: data.value.receiver,
            type: data.value.message_type
        };
        this.communicationLogs.push(logEntry);
        this.renderCommunicationLog(logEntry);

        // Animate on D3 graph
        if (this.networkGraph) {
            this.networkGraph.animateMessage(data.value.emitter, data.value.receiver);
        }
    }

    handleClientConnected(data) {
        const client = {
            username: data.value.username,
            connected_at: data.value.connected_at,
            last_activity: data.value.connected_at,
            status: 'active'
        };

        // Check if already exists
        const existingIndex = this.clients.findIndex(c => c.username === client.username);
        if (existingIndex >= 0) {
            this.clients[existingIndex] = client;
        } else {
            this.clients.push(client);
        }

        this.updateClientCards();
        if (this.networkGraph) {
            this.networkGraph.addClient(data.value.username);
        }
    }

    handleClientDisconnected(data) {
        this.clients = this.clients.filter(c => c.username !== data.value.username);
        this.updateClientCards();
        if (this.networkGraph) {
            this.networkGraph.removeClient(data.value.username);
        }
    }

    handleFullClientList(data) {
        // data.value is an array of client objects with metadata
        this.clients = data.value || [];
        this.updateClientCards();

        if (this.networkGraph) {
            this.networkGraph.setClients(this.clients.map(c => c.username));
        }
    }

    handleClientList(data) {
        // Fallback for simple client list (array of usernames)
        const usernames = data.value || [];
        // Convert to client objects if they're just strings
        if (usernames.length > 0 && typeof usernames[0] === 'string') {
            this.clients = usernames
                .filter(u => u !== 'ADMIN' && !u.startsWith('ADMIN_'))
                .map(username => ({
                    username,
                    connected_at: new Date().toISOString(),
                    last_activity: new Date().toISOString(),
                    status: 'active'
                }));
        }
        this.updateClientCards();

        if (this.networkGraph) {
            this.networkGraph.setClients(this.clients.map(c => c.username));
        }
    }

    renderCommunicationLog(entry) {
        // Remove empty state if present
        const emptyState = this.communicationLog.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }

        const div = document.createElement('div');
        div.className = 'comm-log-entry';

        const time = entry.timestamp.toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        const receiverDisplay = entry.receiver === 'ALL' ? 'Tous' : this.escapeHtml(entry.receiver);

        div.innerHTML = `
            <span class="timestamp">${time}</span>
            <span class="route">
                <span class="emitter">${this.escapeHtml(entry.emitter)}</span>
                <span class="arrow">→</span>
                <span class="receiver">${receiverDisplay}</span>
            </span>
        `;

        this.communicationLog.appendChild(div);
        this.communicationLog.scrollTop = this.communicationLog.scrollHeight;
    }

    updateClientCards() {
        const filteredClients = this.clients.filter(c =>
            c.username !== 'ADMIN' && !c.username.startsWith('ADMIN_')
        );

        this.clientCount.textContent = filteredClients.length;

        if (filteredClients.length === 0) {
            this.clientCards.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">👥</span>
                    <span>Aucun utilisateur connecté</span>
                </div>
            `;
            return;
        }

        this.clientCards.innerHTML = filteredClients.map(client => {
            const connectedTime = this.formatConnectionTime(client.connected_at);
            const statusClass = client.status === 'active' ? 'active' : 'inactive';
            const statusText = client.status === 'active' ? 'En ligne' : 'Inactif';

            return `
                <div class="client-card">
                    <div class="avatar">${client.username[0].toUpperCase()}</div>
                    <div class="info">
                        <div class="name">${this.escapeHtml(client.username)}</div>
                        <div class="connection-time">${connectedTime}</div>
                    </div>
                    <span class="status ${statusClass}">${statusText}</span>
                </div>
            `;
        }).join('');
    }

    formatConnectionTime(isoString) {
        if (!isoString) return 'À l\'instant';

        const connected = new Date(isoString);
        const now = new Date();
        const diff = Math.floor((now - connected) / 1000); // seconds

        if (diff < 60) return 'À l\'instant';
        if (diff < 3600) return `Depuis ${Math.floor(diff / 60)} min`;
        if (diff < 86400) return `Depuis ${Math.floor(diff / 3600)}h`;
        return `Le ${connected.toLocaleDateString('fr-FR')}`;
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    updateConnectionStatus(connected) {
        if (connected) {
            this.statusDot.classList.add('connected');
            this.statusText.textContent = 'En ligne';
            this.connectBtn.disabled = true;
            this.disconnectBtn.disabled = false;
        } else {
            this.statusDot.classList.remove('connected');
            this.statusText.textContent = 'Hors ligne';
            this.connectBtn.disabled = false;
            this.disconnectBtn.disabled = true;
        }
    }

    clearLog() {
        this.communicationLog.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📡</span>
                <span>En attente de messages...</span>
            </div>
        `;
        this.communicationLogs = [];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize admin client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.adminClient = new AdminClient(WS_URL);
});
