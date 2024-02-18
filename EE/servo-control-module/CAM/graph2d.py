from scipy.spatial import KDTree
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

class Graph2D(nx.Graph):

    def __init__(self):
        super().__init__()

    def add_node(self):
        raise NotImplementedError('Use add_point instead.')

    def add_point(self, point:np.array,data:any=None):
        '''
        Add a 2D point to the graph, optionally with data.

        Args:
            point (np.array): 1,2 array of the point coordinates.
            data (any): Optional data to store with the point.
        '''

        # Add the point to the graph
        super().add_node(len(self.nodes),pos=point,data=data)

    def plot(self,title:str=None):
        '''
        Plot the graph.
        '''

        # Get the node positions
        pos = nx.get_node_attributes(self,'pos')

        # Plot the graph
        nx.draw(self,pos,with_labels=True)

        # Add the title
        if title is not None:
            plt.title(title)

        plt.show()

    def link_by_radius(self,radius:float,eps:float=1e-4):
        '''
        Link any unlinked nodes in the graph based on a radius.

        Args:
            radius (float): Maximum distance to link nodes.
        '''

        # Get subgraph of unlinked nodes
        nodes_without_edges = [node for node, degree in self.degree() if degree == 0]

        # Extract the subgraph of the nodes without edges
        subgraph = self.subgraph(nodes_without_edges)

        # Get the node positions
        pos = nx.get_node_attributes(subgraph,'pos')

        # Create a KDTree for the nodes
        kdtree = KDTree(list(pos.values()))

        # Get the links
        links = kdtree.query_pairs(radius, eps=eps)

        # The KD tree is likely a subset of the graph, so we need to map the indices back to the graph
        links = [(list(pos.keys())[i],list(pos.keys())[j]) for i,j in links]

        # Add the links to the graph
        self.add_edges_from(links)

    def link_components(self,xy:np.array):
        '''
        Link the components of the graph.
        '''

        if not isinstance(xy,np.ndarray):
            raise ValueError('xy must be a numpy array.')
        # if xy.shape[1]!=2:
        #     raise ValueError('xy must be a 2D array.')

        # For each component, extract the end points.
        comp_ends = []
        for component in nx.connected_components(self):

            # Get the end points
            end_points = [node for node in component if self.degree(node)==1]

            # Add the end points to the component
            comp_ends.append(end_points)

        print(comp_ends)

        # Get the min dist from the start point to all ends.
        # This doesn't work
        dist = [self.dist_from_point(xy,i) for i in comp_ends]
        print(dist)

        # From a starting point, look for the end of each component that's closest.
        # Add that index to the list, then the index of the other end to the list.
        # Find the distance from other end to all other component ends.
        raise NotImplementedError('Not fully implemented yet.')

    def dist_from_point(self,point:np.array,index:int)->np.array:
        '''
        Get the distance from a 2D point to a specific index point.

        Args:
            point (np.array): 1,2 array of the point coordinates.
            index (int): Index of the node to get the distance to.

        Returns:
            np.array: Array of distances to the nodes.
        '''

        # Get the node positions
        pos = nx.get_node_attributes(self,'pos')

        # Get the distances
        return np.linalg.norm(point-pos[index])

    def dist(self,idx1:int,idx2:int)->float:
        '''
        Get the distance between two nodes.

        Args:
            idx1 (int): Index of the first node.
            idx2 (int): Index of the second node.

        Returns:
            float: Distance between the nodes.
        '''

        # Get the node positions
        pos = nx.get_node_attributes(self,'pos')

        # Get the distance
        return np.linalg.norm(pos[idx1]-pos[idx2])