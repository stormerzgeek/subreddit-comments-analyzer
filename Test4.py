import praw
import networkx as nx
import matplotlib.pyplot as plt
import mpld3
from flask import Flask
from flask import render_template
from flask import request
import os
import community.community_louvain as community

TEMPLATE_DIR = os.path.abspath('./templates')
STATIC_DIR = os.path.abspath('./static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
#app = Flask(__name__)

redditApi = praw.Reddit(client_id='ehGX8eI976F8BsGzFy1PiQ', client_secret='ESUoHqETagk3jbp3NXBwy2OsgS9WsQ', user_agent='subreddit analysis by u/stormerzgeek')

def recursive_node_adder(g, comment, parent_author):
    '''Recursively process comments and add them to the graph'''
    
    # Check if we have the node already in our graph
    if comment.author!=None:
        if comment.author not in g.nodes:
            g.add_node(comment.author)
        # Create an edge between this comment author and the parent author
        g.add_edge(comment.author, parent_author)
        # Iterate through the comments
        for reply in comment.replies.list():
            if isinstance(reply, praw.models.MoreComments):
                continue
            # Recursively process this reply
            recursive_node_adder(g, reply, comment.author)
# Create an undirected graph
def generate_graph(subreddit_name,postsno,sorting):
    g = nx.Graph()
    subreddit = subreddit_name
    breadthCommentCount = 10
    targetSub = redditApi.subreddit(subreddit)
    if sorting=="hot":  
        submissions = targetSub.hot(limit=postsno)
    elif sorting=="new":
        submissions = targetSub.new(limit=postsno)
    elif sorting=="top":
        submissions = targetSub.top(limit=postsno)
    for post in submissions:
        #print (post.author, "-", post.title)
        # Check if we have the node already in our graph
        if post.author!=None:
            if post.author not in g.nodes:
                g.add_node(post.author)
            post.comment_limit = breadthCommentCount
            # Get the top few comments
            for comment in post.comments.list():
                # Skip MoreComment objects, which don't have authors
                if isinstance(comment, praw.models.MoreComments):
                    continue
                # Recursively process this reply
                recursive_node_adder(g, comment, post.author)
    global gendata
    gendata = g

def plotgraph(g,type,label):
    #fig, ax = plt.subplots()
    fig = plt.figure(figsize=(10, 8))
    ax = fig.subplots()
    pos = nx.spring_layout(g, scale=200, iterations=5, k=0.2)
    pos_fr = nx.fruchterman_reingold_layout(g)
    # And draw the graph with node labels
    print(label)
    if(type == "spring" and label == "true"):
        nx.draw(g,pos,ax=ax, node_color='red', width=1, with_labels=True, node_size=200)
    elif(type == "spring" and label == "false"):
        nx.draw(g,pos,ax=ax, node_color='red', width=1, with_labels=False, node_size=200)
    elif(type == "random" and label == "true"):
        nx.draw_random(g,ax=ax, node_color='red', width=1, with_labels=True, node_size=200)
    elif(type == "random" and label == "false"):
        nx.draw_random(g,ax=ax, node_color='red', width=1, with_labels=False, node_size=200)
    elif(type == "circular" and label == "true"):
        nx.draw_circular(g,ax=ax, node_color='red', width=1, with_labels=True, node_size=200)
    elif(type == "circular" and label == "false"):
        nx.draw_circular(g,ax=ax, node_color='red', width=1, with_labels=False, node_size=200)
    elif(type == "shell" and label == "true"):
        nx.draw_shell(g,ax=ax, node_color='red', width=1, with_labels=True, node_size=200)
    elif(type == "shell" and label == "false"):
        nx.draw_shell(g,ax=ax, node_color='red', width=1, with_labels=False, node_size=200)
    elif(type == "spectral" and label == "true"):
         nx.draw_spectral(g,ax=ax, node_color='red', width=1, with_labels=True, node_size=200)
    elif(type == "spectral" and label == "false"):
        nx.draw_spectral(g,ax=ax, node_color='red', width=1, with_labels=False, node_size=200)
    elif(type == "fr" and label == "true"):
        nx.draw(g,pos_fr,ax=ax, node_color='red', width=1, with_labels=True, node_size=200)
    elif(type == "fr" and label == "false"):
        nx.draw(g,pos_fr,ax=ax, node_color='red', width=1, with_labels=False, node_size=200)
    elif(type == "comdet"):
        parts = community.best_partition(g)
        values = [parts.get(node) for node in g.nodes()]
        plt.axis("off")
        if(label=="false"):
            nx.draw_networkx(g, pos = pos, cmap = plt.get_cmap("jet"), node_color = values, node_size = 200, with_labels = False)
        elif(label=="true"):
            nx.draw_networkx(g, pos = pos, cmap = plt.get_cmap("jet"), node_color = values, node_size = 200, with_labels = True)
    #plt.show()
    html_graph = mpld3.fig_to_html(fig)
    edges=g.number_of_edges()
    nodes=g.number_of_nodes()
    return html_graph,edges,nodes

def dcentral(g):
    value = nx.degree_centrality(g)
    #values=[(x,centrality[x]) for x in sorted(centrality,key=centrality.get,reverse=False)]
    return value

def bcentral(g):
    value = nx.betweenness_centrality(g)
    return value

def ccentral(g):
    value = nx.closeness_centrality(g)
    return value

def density(g):
    value = nx.density(g)
    value_dict={"Density":value}
    return value_dict

def transitivity(g):
    value = nx.transitivity(g)
    value_dict={"Global Coefficinet (Transitivity)":value}
    return value_dict

def degree(g):
    value = {node:val for (node, val) in g.degree()}
    return value

def graphdownload(g,name):
    filename = name+".graphml"
    nx.write_graphml(g, filename, prettyprint=True)



@app.route('/')
def index():
    return render_template('index.html')



@app.route('/graph', methods=["GET","POST"])
def graph():
    global subreddit_name
    subreddit_name=request.form["subreddit"]
    postsno=int(request.form["postsno"])
    sorting=request.form["sorttype"]
    type=request.form["graphtype"]
    label=request.form["labelreq"]
    generate_graph(subreddit_name,postsno,sorting)
    html_graph,numedges,numnodes=plotgraph(gendata,type,label)
    return render_template('graph.html', subreddit_name=subreddit_name, html_graph=html_graph,numedges=numedges,numnodes=numnodes)


@app.route('/measures', methods=["GET","POST"])
def measures():
    measure_type=request.form["measures"]
    if(measure_type == 'DCentrality'):
        type_name="Degree Centrality"
        head_tag="Reddit Username"
        sortstat="(Click to sort)"
        values=dcentral(gendata)
    elif(measure_type == 'BCentrality'):
        type_name="Betweeness Centrality"
        head_tag="Reddit Username"
        sortstat="(Click to sort)"
        values=bcentral(gendata)
    elif(measure_type == 'CCentrality'):
        type_name="Closeness Centrality"
        head_tag="Reddit Username"
        sortstat="(Click to sort)"
        values=bcentral(gendata)
    elif(measure_type == "Density"):
        type_name = " "
        head_tag=" "
        sortstat=" "
        values=density(gendata)
    elif(measure_type == "Transitivity"):
        type_name = " "
        head_tag = " "
        sortstat = " "
        values=transitivity(gendata)
    elif(measure_type == 'Degree'):
        type_name="Degree of each node"
        head_tag="Reddit Username"
        sortstat="(Click to sort)"
        values=degree(gendata)
    #html_graph=plotgraph(finalgraph)
    return render_template('measures.html', type_name=type_name, values=values,head_tag=head_tag,sortstat=sortstat)

@app.route('/download', methods=["GET","POST"])
def download():
    graphdownload(gendata,subreddit_name)
    return render_template('downloaded.html',subreddit_name=subreddit_name)
    
if __name__ == '__main__':
    app.run(debug=True)
