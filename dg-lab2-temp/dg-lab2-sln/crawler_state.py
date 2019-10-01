import json
from collections import deque


class CrawlerState:
    """
    Encapsulates the crawler state information, managing the open queue and the visited list.

    Variables
    _depth_limit -- The maximum depth of nodes from the start
    _next_id -- The id to assign to the next node
    _open -- The queue holding nodes yet to be expanded
    _visited0 -- The dictionary marking items type 0 as visited. Note that we cannot use node ids because those are
        always unique. The label must be something that identifies the node uniquely like a user id or post id, etc.
        These will then be recognized when the application returns them in response to a later query.
    _visited1 -- Same as above for type 1.
    """

    _depth_limit = 1
    _next_id = 100
    _open = None
    _visited0 = None
    _visited1 = None

    def __init__(self, depth_limit=1):
        """
        Initializes the data structures for the crawler

        Keyword arguments
        depth_limit -- Depth of the crawl (default 1)
        """
        self._depth_limit = depth_limit
        self._open = deque()
        self._visited0 = {}
        self._visited1 = {}

    def from_file(self, filename):
        """
        Creates the crawler state from a file, which is assumed to be in the correct JSON format.
        """
        with open(filename) as f:
            jdata = json.load(f)
            self.from_json(jdata)

    def from_json(self, json_data):
        """
        Creates the crawler state from a JSON object.

        JSON format for a crawl is a dictionary with keys next_id, depth_limit, visited_b0, visited_b1, open.
        open is stored as a list.
        """
        self._depth_limit = json_data["depth_limit"]
        self._next_id = json_data["next_id"]
        self._open = deque(json_data["open"])
        self._visited0 = json_data["visited0"]
        self._visited1 = json_data["visited1"]

    def from_net(self, net, depth):
        """
        Creates a crawler state from a network.

        Only guaranteed to work if the network was constructed by a previous
        crawl and if the crawl was complete -- that is that the nodes with
        the maximum depth are the only ones on the open queue. Otherwise, you need
        to save the crawler state and the network.
        """
        # This is the new depth of crawl
        self._depth_limit = depth
        # Find the maximum id and add 1 to create next_id
        self._next_id = max([int(node) for node in net.nodes()]) + 1
        # Add all the node API calls to the visited set
        self._visited0 = {data['label']: node for node, data in net.nodes(data=True) if
                          data['bipartite'] == 0}
        self._visited1 = {data['label']: node for node, data in net.nodes(data=True) if
                          data['bipartite'] == 1}
        # Get the nodes with maximum depth, add to the open list.
        max_depth = max([node_data['_depth']
                         for node, node_data in net.nodes(data=True)])
        self._open = deque([node for node, data in net.nodes(data=True)
                            if data['_depth'] == max_depth])

    def to_file(self, filename):
        """
        Saves the crawler state in a JSON file
        """
        with open(filename, 'w') as f:
            output = self.to_json()
            f.write(output)

    def to_json(self):
        """
        Creates a JSON object representing the crawl
        """
        data = {'next_id': self._next_id,
                'depth_limit': self._depth_limit,
                'visited0': self._visited0,
                'visited1': self._visited1,
                'open': list(self._open)}
        return json.dumps(data)

    def next_id(self):
        """
        Gets the next node id
        """
        nid = self._next_id
        self._next_id = self._next_id + 1
        return nid

    def is_completed(self):
        """
        Returns true if the _open queue is empty.
        """
        return len(self._open) == 0

    def next_node(self):
        """
        Gets the next node from the queue.
        """
        return self._open.popleft()

    def put_back(self, net, node):
        """
        Returns a removed node to the queue.

        Necessary if expansion fails and needs to be retried later.
        """
        net.node[node]['_expanded'] = 0
        self._open.appendleft(node)

    def is_visited(self, bipartite, label):
        """
        Returns true if the label is in the visited dictionary.
        """
        if bipartite == 0:
            return label in self._visited0
        else:
            return label in self._visited1

    def visited_node(self, bipartite, label):
        """
        Returns the node associated with the label

        Does not check that the query is actually in the dictionary. Check using is_visited() first.
        """
        if bipartite == 0:
            return self._visited0[label]
        else:
            return self._visited1[label]

    def add_visited(self, label, bipartite, node):
        """
        Adds the name, node pair to the visited dictionary.
        """
        if bipartite == 0:
            self._visited0[label] = node
        else:
            self._visited1[label] = node

    def add_open(self, node):
        """
        Adds a new node to the queue for later expansion
        """
        self._open.append(node)

    def is_legal_depth(self, d):
        """
        Returns true if d is within the depth limit.
        """
        return d <= self._depth_limit

    def set_depth_limit(self, limit):
        self._depth_limit = limit
