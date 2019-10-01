import urllib.parse
import urllib.request
import json
import pandas as pd
import re
from gastrodon import RemoteEndpoint,QName,ttl,URIRef,inline, GastrodonException
from crawler_abst_api import CrawlerAbstractAPI



class MyAPI (CrawlerAbstractAPI):
    """
    Encapsulates the interactions for the API used in lab.
    There are people and movies. Person is bipartite 0. movies bipartite 1.

    Variables
    _baseUrl -- This is the URL that access the API interface
    _delay -- Number of seconds to wait between API calls
    
    """
    
    _baseUrl = "http://josquin.cti.depaul.edu/~rburke/cgi-bin/"
    _actorQuery = "get-users.py?q={}"
    _movieQuery = "get-tags.py?q={}"
    _actorErrorTest = "get-users.py?q={}&ErrRate=100"
    
    #gathered from http://dbpedia.org/sparql?help=nsdecl
    prefixes=inline("""
        @prefix : <http://dbpedia.org/resource/> .
        @prefix dbo: <http://dbpedia.org/ontology/> .
        @prefix dbp: <http://dbpedia.org/property/> .
        @prefix dbc: <http://dbpedia.org/resource/Category:> .
        @prefix dbr: <http://dbpedia.org/resource/> .
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .

    """).graph
    
    _endpoint=RemoteEndpoint(
        "http://dbpedia.org/sparql/"
        ,default_graph="http://dbpedia.org"
        ,prefixes=prefixes
        ,base_uri="http://dbpedia.org/resource/"
    )
    
    

    def initial_nodes(self): #DONE DO NOT TOUCH--------------------------------------
        initial_actor = '<Dwayne_Johnson>'

        # You might have make a query to get the attribute here.
        return [(initial_actor, self.make_node_actor(initial_actor,"male", 0))]

    def make_actors_url(self, movie): #DONE DO NOT TOUCH--------------------------------------
        #This is supposed to return a URL that GIVES actors
        """
        Returns a URL that can be used to issue the query.

        Arguments
        query -- a string to be passed to the API
        """
        specialCase = False;
        #Step 1, slice of brackets < >
        #movie = movie[1:-1]
        #print(movie)
        #Step 2, check if movie has special characters
        if((re.search( '[*\(\)\.\:]', movie)) != None):
            specialCase = True
        #print(specialCase)
        
        if(specialCase):
            query = ["""SELECT ?actor ?gender  WHERE {   
            <http://dbpedia.org/resource/""",movie,"""> dbo:starring ?actor
            OPTIONAL{
                ?actor foaf:gender ?gender
            }
            }"""]
        else:                
            query = ["""SELECT ?actor ?gender  WHERE {   
            dbr:""",movie,""" dbo:starring ?actor
            OPTIONAL{
                ?actor foaf:gender ?gender
            }
            }"""]

        query = ''.join(query)
        #print(query)
        #print(self._endpoint.select(query))
        return query;

    def make_movies_url(self, actor): #DONE DO NOT TOUCH--------------------------------------
        #This is supposed to return a URL that GIVES movies
        """
        Returns a URL that can be used to issue the query.

        Arguments
        query -- a string to be passed to the API
        """
        specialCase = False;
        #print(actor)
        #Step 2, check if actor has special characters
        if((re.search( '[*\(\)\.\:]', actor)) != None):
            specialCase = True
        #print(specialCase)
        
        if(specialCase):
            query = ["""
            SELECT ?movie ?budget ?gross 
            WHERE {
            ?movie rdf:type dbo:Film .
            ?movie dbo:starring <http://dbpedia.org/resource/""",actor,""">
            OPTIONAL {
                ?movie dbo:gross ?gross
                
            } OPTIONAL{
            ?movie dbo:budget ?budget
            }
            }
            """]
        else:
            query = ["""
            SELECT ?movie ?budget ?gross 
            WHERE {
            ?movie rdf:type dbo:Film .
            ?movie dbo:starring dbr:""",actor, """ .
            OPTIONAL {
                ?movie dbo:gross ?gross                   
            } OPTIONAL{
            ?movie dbo:budget ?budget
            }
            }
            """]


        query = ''.join(query)
        #print("printing query" + query)
        #print("Printing endpoint:")
        #print(self._endpoint.select(query))
        return query;

    def make_node_actor(self, actor, gender, depth): #DONE DO NOT TOUCH--------------------------------------
        """
        Makes a node representing a user

        Arguments
        id -- the node id (converted to a string)
        actor -- user actor
        movie -- the user's movie
        depth -- depth of the search to this point
        graph -- Graph object to add the node to
        """
        nid = super().make_node(0, actor, depth)
        self._graph.nodes[nid]['gender'] = gender
        return nid

    def make_node_movie(self, movie, budget, gross, depth): #DONE DO NOT TOUCH-----------------------------
        """
        Makes a node representing a movie

        Arguments
        id -- the node id (converted to a string)
        movie -- the movie string
        depth -- depth of the search to this point
        graph -- Graph object to add the node to
        """
        nid = super().make_node(1, movie, depth)
        self._graph.nodes[nid]['gross'] = gross
        self._graph.nodes[nid]['budget'] = budget
        return nid

    def execute_actors_query(self, movie): #DONE DO NOT TOUCH-----------------------------
        """
        Executes the actors query and parses the results.

        Arguments
        movie -- a movie

        Returns
        (success flag, data) -- tuple
        success flag -- true if the values were successfully parsed (no errors)
        data -- a list of (actor, gender) pairs that resulted from the query
        """
        #slice of brackets < >
        movie = movie[1:-1]
        #get the query (we know this works) (kinda)
        query = self.make_actors_url(movie)
        try:           
            #Call gastrodon here

            ########### - throws GastrodonException
            roughDataFrame = self._endpoint.select(query)
            if(roughDataFrame.empty):
                return False
            ###########
            
            #this gives us panda framework
            #print((roughDataFrame))
            #convert to strings
            roughDataFrame['actor'] = roughDataFrame['actor'].astype(str)
            roughDataFrame['gender'] = roughDataFrame['gender'].astype(str)
            #print(roughDataFrame)

            data = []        
            for index,actor,gender in roughDataFrame.itertuples():
                data.append((actor,gender))
                #print(gender)
            return((True,data))
        except GastrodonException as e:
            return False
        #except QueryBadFormed as e:
            #return False
            
    def execute_movies_query(self, actor): #DONE DO NOT TOUCH-----------------------------
        """
        Executes the movies query and parses the results.

        Arguments
        actor -- a user actor

        Returns
        (success flag, data) -- tuple
        success flag -- true if the values were successfully parsed (no errors)
        data -- a list of movies that resulted from the query
        """
        #-----------------------------------------------
        #slice of brackets < >
        actor = actor[1:-1]
        #get the query (we know this works) (kinda)
        query = self.make_movies_url(actor)
        try:           
            #Call gastrodon here

            ########### - throws GastrodonException
            roughDataFrame = self._endpoint.select(query)
            #check if it's empty
            if(roughDataFrame.empty):
                return False
            ###########
            
            #this gives us panda framework
            #print((roughDataFrame))
            #convert to strings
            roughDataFrame['movie'] = roughDataFrame['movie'].astype(str)
            roughDataFrame['budget'] = roughDataFrame['budget'].astype(float)
            roughDataFrame['gross'] = roughDataFrame['gross'].astype(float)
            #print(roughDataFrame)

            data = []        
            for index,movie,gross,budget in roughDataFrame.itertuples():
                data.append( {'movie':movie, 'gross':gross, 'budget':budget })           
            return (True, data)
        #-----------------------------------------------
        except GastrodonException as e:          
            return False
        #except QueryBadFormed as e:
            #return False

    # These are Movies bipartite 1
    def get_child0(self, node, graph, state):
        actor = graph.node[node]['label']
        success, data = self.execute_movies_query(actor)

        if success:
            # Distinguish nodes previously seen from new nodes
            old_movies = [node['movie'] for node in data if state.is_visited(1, node['movie'])]
            new_movies = [(node['movie'],node['budget'],node['gross']) for node in data if not (state.is_visited(1, node['movie']))]
            #-----------------------------------------------
            #print(new_movies)
            # Get the existing nodes
            old_nodes = [state.visited_node(1, movie) for movie in old_movies]
            #-----------------------------------------------
            # Create the new nodes
            new_depth = graph.node[node]['_depth'] + 1
            new_nodes = [self.make_node_movie(movie,budget,gross , new_depth)for movie, budget, gross in new_movies]
            # Return the dict with the info
            #-----------------------------------------------
            return {'success': True, 'new': new_nodes, 'old': old_nodes}
        else:
            return {'success': False}

    # These are Actors bipartite 0
    def get_child1(self, node, graph, state):
        movie = graph.nodes[node]['label']
        success, data = self.execute_actors_query(movie)

        if success:
            # Distinguish nodes previously seen from new nodes
            old_actors = [actor for actor, movie in data if state.is_visited(0, actor)]
            new_actors = [(actor, gender) for actor, gender in data
                         if not (state.is_visited(0, actor))]

            #print(new_actors)
            old_nodes = [state.visited_node(0, actor) for actor in old_actors]
            
            new_depth = graph.node[node]['_depth'] + 1
            new_nodes = [self.make_node_actor(actor, gender,new_depth)
                         for actor, gender in new_actors]
            return {'success': True, 'new': new_nodes, 'old': old_nodes}
        else:
            return {'success': False}
