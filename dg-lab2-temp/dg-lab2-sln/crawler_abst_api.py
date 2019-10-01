import time
from abc import ABC, abstractmethod


class CrawlerAbstractAPI(ABC):
    """
    Encapsulates the interactions with the API from which you are gathering data.
    Note that the CrawlerAPI does not hold any state, so it does not need to be saved when the state is saved.
    This class assumes that you are crawling a bipartite network with nodes of type 0 and 1.

    Variables
    _delay: Wait (seconds) in betweem API calls
    _ERROR_RESULT: What the API returns in case of error
    """

    _delay = 0.5

    _ERROR_RESULT = (False, [])

    _state = None
    _graph = None

    def __init__(self):
        super().__init__()

    def set_state(self, state):
        self._state = state

    def set_graph(self, graph):
        self._graph = graph

    def sleep(self):
        """
        Sleeps for the _delay interval (secs) to avoid overtaxing the API
        """
        time.sleep(self._delay)

    def make_node(self, node_type, label, depth):
        """
        Makes a node representing a user

        Arguments
        node_type -- the type of node (0 or 1)
        state -- the current graph state
        """

        nid = str(self._state.next_id())
        self._graph.add_node(nid, label=label, bipartite=node_type, _depth=depth,  _expanded=0)
        return nid

    def node_label(self, nid):
        return self._state.graph.nodes[nid]['label']

    def is_visited(self, node_type, label):
        self._state.is_visited(node_type, label)

    def visited_node(self, node_type, label):
        self._state.visited_node(node_type, label)

    @abstractmethod
    def initial_nodes(self):
        """
        Creates the initial nodes that are the starting point for the crawl.

        :return: A list of label, node pairs to initialize the search
        """
        pass

    @abstractmethod
    def get_child0(self, node, graph, state, new_depth):
        pass

    @abstractmethod
    def get_child1(self, node, graph, state, new_depth):
        pass

    def get_children(self, node, crawler):
        """
        Gets children of the node based on API.

        Arguments
        node -- the node to expand
        crawler -- the Crawler object, needed to access the graph and other aspects of the crawl state

        Returns
        a dictionary
        success: True if the API call was successful
        if successful
        new: a list of new nodes that are children of node
        old: a list of old nodes that are children of node
        """

        graph = crawler.get_graph()
        state = crawler.get_state()
        self.sleep()
        if graph.node[node]['bipartite'] == 0:
            return self.get_child0(node, graph, state)

        else:
            return self.get_child1(node, graph, state)
