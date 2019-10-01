import networkx as nx
import argparse

from crawler_my_api import MyAPI
from crawler_state import CrawlerState


class Crawler:
    """
    Manages the crawling process. It can be run from the command line or imported and the methods used.
    Sample command line:
    crawler.py 2 5 out.graphml out.json

    The Crawler function depends on the implementation of an API class, which is a subclass of the CrawlerAbstractAPI
    class. This must implemented fresh for every new API to be crawled. You should not need to edit this code at all.

    Variables:
    _state -- A CrawlerState object encapsulating the current state of the crawl
    _net -- A NetworkX Graph object containing the network gather so far
    _api -- The API object, a concrete instance of a subclass of CrawlerAbstractAPI
    _autosave_interval -- The number of nodes to be added in between autosaves. A large number (~100) recommended
    _autosave_path -- The path where autosave files are stored.
    _max_fail -- The number of failures before the crawler will exit.
    """

    _state = None
    _net = None
    _api = None
    _autosave_interval = -1             # No autosaving by default (configurable)
    _autosave_path = ""
    _max_fail = 3                       # Allow 3 failures (configurable)

    def __init__(self, depth_limit, api):
        """
        Sets up the data structures for the crawl
        """
        self._state = CrawlerState(depth_limit)
        self._net = nx.Graph()
        self._api = api
        self._api.set_state(self._state)
        self._api.set_graph(self._net)

    def get_state(self): return self._state

    def get_graph(self): return self._net

    def get_api(self): return self._api

    def from_files(self, graph_file, state_file):
        """
        Creates a crawl from a pair of files. No error checking is performed to make sure the files match.

        Arguments
        graph_file -- a GraphML file containing a network created in a previous crawl.
        state_file -- a JSON file containing the serialized CrawlerState.
        """
        state = CrawlerState()
        state.from_file(state_file)
        self._state = state
        self._net = nx.read_graphml(graph_file)  
        self._api.set_state(self._state)
        self._api.set_graph(self._net)

    def from_net(self, net, depth_limit):
        """
        Create a crawl from an existing network. Assumes that all nodes at maximum depth need to be expanded.

        Arguments
        net -- a Graph object from a previous crawl.
        depth_limit -- the new depth limit for crawling.
        """
        state = CrawlerState()
        state.from_net(net, depth_limit)
        self._state = state
        self._net = net
        self._api.set_state(self._state)
        self._api.set_graph(self._net)

    def to_files(self, net_file, state_file):
        """
        Saves the state of the crawl.

        Arguments
        net_file -- name for the graphml file for the network part
        state_file -- name for the JSON file for the CrawlerState
        """
        nx.write_graphml(self._net, net_file)
        self._state.to_file(state_file)

    def set_depth_limit(self, limit):
        self._state.set_depth_limit(limit)

    def initialize(self):
        """
        Create initial nodes to start the crawl and set up the data structures

        """

        for label, node in self._api.initial_nodes():

            # We don't want to create another copy of the start point, so we add to the visited set.
            self._state.add_visited(label, 0, node)

            # Add to open queue to initialize search
            self._state.add_open(node)

    def expand_node(self, node):
        """
        Expands a node by getting its children via the API and adding them to the graph
        """
        print("Expanding node: %s" % node)
        ndepth = self._net.nodes[node]['_depth']
        # Don't expand a node at the maximum legal depth
        if not (self._state.is_legal_depth(ndepth + 1)):
            return True
        else:
            # Query the API
            result = self._api.get_children(node, self)
            if result['success']:
                for old_node in result['old']:
                    # Link existing nodes
                    self._net.add_edge(node, old_node)
                for new_node in result['new']:
                    # Link new nodes
                    self._net.add_edge(node, new_node)
                    # Add to visited set
                    label = self._net.nodes[new_node]['label']
                    bipartite = self._net.nodes[new_node]['bipartite']
                    self._state.add_visited(label, bipartite, new_node)
                    # Add new nodes to queue
                    self._state.add_open(new_node)
                # Mark parent as expanded
                self._net.nodes[node]['_expanded'] = 1
                return True
            else:  # The API call failed
                return False

    def set_autosave(self, interval, path):
        """
        Sets up the parameters of the autosave capability

        Arguments
        interval -- number of nodes to expand in between autosaves.
        path -- the path to save the crawler files. The files are named autosave.graphml and autosave.json.
        """
        self._autosave_path = path
        self._autosave_interval = interval

    def crawl_k(self, k):
        """
        Build the network by expanding up to k nodes (but not beyond the depth limit). Halts
        if it encounters more than _max_fail errors trying to expand the same node.

        Arguments
        k -- the number of nodes to expand
        """
        node_count = 0
        fail_count = 0
        while node_count < k and (not self.is_completed()):
            node = self._state.next_node()
            if self.expand_node(node):
                fail_count = 0
                node_count = node_count + 1
                if (self._autosave_interval > 0 and
                        node_count % self._autosave_interval == 0):
                    print("Autosaving...")
                    self.to_files(self._autosave_path + "autosave.graphml",
                                  self._autosave_path + "autosave.json")
            else:
                fail_count = fail_count + 1
                # Put the node back on the queue to try again
                self._state.put_back(self._net, node)
                print("API call failed on node %s. Error %i." % (node, fail_count))
                print(self._net.nodes[node])
                # Exit if we fail too many times
                if fail_count > self._max_fail:
                    return False
        return True

    def is_completed(self):
        """
        Returns true if all the nodes of depth_limit have been generated (but not expanded)
        """
        return self._state.is_completed()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    # Required args
    parser.add_argument('depth', type=int, help="Maximum depth of the crawl")
    parser.add_argument('k', type=int, help="Number of nodes to crawl")
    parser.add_argument('graphfile', help="File to store the resulting graph")
    parser.add_argument('statefile', help="File to store the final search state")

    # Optional args
    parser.add_argument('-o', '--old', nargs=2, required=False,
                        help="Files containing starting graph and starting point for search, saved from prior crawling")
    parser.add_argument('-f', '--fail', type=int,
                        help="Number of API failures allowed before halting (default 3)")
    parser.add_argument('-a', '--auto', type=int,
                        help="Number of nodes to expand between autosaves (default -1 = no autosave)")

    args = parser.parse_args()
    dictargs = vars(args)

    depth = dictargs['depth']
    num_nodes = dictargs['k']
    graph_filename = dictargs['graphfile']
    state_filename = dictargs['statefile']

    # Set up the Crawler
    api = MyAPI()
    crawler = Crawler(depth, api)

    # If loading a previous crawl
    if dictargs['old'] is not None:
        old_graph_filename, old_state_filename = dictargs['old']
        crawler.from_files(old_graph_filename, old_state_filename)
        # This is needed because the old state may have had a different depth
        crawler.set_depth_limit(depth)
    else:
        crawler.initialize()

    # Execute the crawl
    crawler.crawl_k(num_nodes)
    # Save the results
    crawler.to_files(graph_filename, state_filename)
