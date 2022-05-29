# Date: May 14th 2021
# Author: Changlong Yu <cyuaq # cse.ust.hk>

import os 
import sys
import json
import pickle
import networkx as nx
import numpy as np

rel2id = dict()
id2rel = ["Precedence", "Succession", "Synchronous",
          "Reason", "Result", "Condition", "Contrast", 
          "Concession", "Conjunction", "Instantiation", 
          "Restatement", "ChosenAlternative", "Alternative", 
          "Exception", "Co_Occurrence"]

for i,rel in enumerate(id2rel):
    rel2id[rel] = i

def preprocess(data_dir):

    event_dict = dict()
    event_file = open(data_dir + "event_info_sorted.txt")
    while True:
        line = event_file.readline()
        if not line:
            break
        if len(line.strip().split("|")) > 6:
            print(line)
            continue 
        e_id, freq, pattern, _, skeleton, word = line.strip().split("|")
        if e_id not in event_dict:
            event_dict[e_id] = [freq, pattern, skeleton, word]
        else:
            continue
    
    print(len(event_dict))
    event_file.close()

    relation_file = open(data_dir +"relation_info.txt")
    relation_detailed = open(data_dir + "relation_info_with_event.txt", "w")
    co_occur_relation = open(data_dir + "co_occur_relation_info_with_event.txt", "w")

    relation_json = open(data_dir + "direct_relation_edge.jsonl", "w")

    selected_pair = 0
    all_pair = 0
    only_cooccur = 0

    event_freq = dict()
    relation_freq = dict()
    while True:
        line = relation_file.readline()
        if not line:
            break
        all_pair +=1 
        r_id, lid, rid = line.strip().split("|")[:3]
        scores = line.strip().split("|")[3:]
        assert len(scores) == len(rel2id)
        all_rel = [[i,each] for i, each in enumerate(scores) if each!="0.0"]
        tmp_dict = dict()

        if lid in event_dict and rid in event_dict:
            selected_pair +=1
            tmp_dict["e1_id"] = lid
            tmp_dict["e2_id"] = rid
            tmp_dict["e1"] = event_dict[lid][3]
            tmp_dict["e2"] = event_dict[rid][3]
            tmp_dict["rels"] = dict()
            for r, p in all_rel:
                tmp_dict["rels"][id2rel[r]] = p 

            if lid not in event_freq:
                event_freq[lid] =len(all_rel)
            else:
                event_freq[lid]+=len(all_rel)
            
            if rid not in event_freq:
                event_freq[rid] = len(all_rel)
                event_freq[rid] += len(all_rel)
            
            if len(all_rel)==1:
                if id2rel[all_rel[0][0]] != "Co_Occurrence":
                    print(line)
                only_cooccur +=1
                co_occur_relation.write(lid + "\t" + rid + "\t" + event_dict[lid][3] + "\t" + event_dict[rid][3] + "\t" +  id2rel[all_rel[0][0]] +"\t" + all_rel[0][1] +"\n")
            else:
                for (j,s) in all_rel:
                    if id2rel[j] not in relation_freq:
                        relation_freq[id2rel[j]] = 1
                    else:
                        relation_freq[id2rel[j]]+=1
                    relation_detailed.write(lid + "\t" + rid + "\t" + event_dict[lid][3] + "\t" + event_dict[rid][3] + "\t" + id2rel[j] +"\t"+ s +"\n")
            
            json.dump(tmp_dict, relation_json)
            relation_json.write("\n")

    print(selected_pair, all_pair)
    # 12,942,207 20,204,994
    print("Only co-occured event: ", only_cooccur) 
    # Only co-occured event: 9,397,080
    relation_file.close()
    relation_detailed.close()
    co_occur_relation.close()

    event_vocab = open(data_dir + "graph/event_vocab.txt","w")
    for k, v in sorted(event_freq.items(), key= lambda item:item[1], reverse=True):
        event_vocab.write(k + "\t" + event_dict[k][3] + "\t" + str(v) + "\n")
    
    event_vocab.close()
    print(relation_freq)
    
    # {'Precedence': 319087, 'Reason': 273824, 'Result': 281939, 
    # 'Condition': 445549, 'Contrast': 1019590, 'Concession': 68372, 
    # 'Conjunction': 1753760, 'Restatement': 12379, 'ChosenAlternative': 5280, 
    # 'Alternative': 101089, 'Co_Occurrence': 3545127, 'Succession': 94530, 
    # 'Instantiation': 5914, 'Exception': 2807}

def save_pickled_graph(data_dir):
    
    event2id = open(data_dir + "graph/event_vocab.txt").readlines()
    event2id_dict = dict()

    event_dict_freq = dict()
    event_dict_freq["aid2word"] = dict()
    event_dict_freq["eid2aid"] = list()
    
    for i, line in enumerate(event2id):
        event2id_dict[line.strip().split("\t")[0]] = i
        event_dict_freq["eid2aid"].append(line.strip().split("\t")[0])
        event_dict_freq["aid2word"][line.strip().split("\t")[0]] = line.strip().split("\t")[1]
        
    event_dict_freq["aid2eid"] = event2id_dict
    print(len(event2id_dict))

    event_pickle = open(data_dir + "graph/event_vocab.pkl","wb")
    pickle.dump(event_dict_freq, event_pickle)

    aser_core_graph = open( data_dir + "graph/aser_core_graph.dat", "w")
    aser_graph = open( data_dir + "relation_info_with_event.txt")

    while True:
        line = aser_graph.readline()
        if not line:
            break
        e1, e2, _, _, rel, _ = line.strip().split('\t')
        aser_core_graph.write(str(event2id_dict[e1]) + "\t" + str(event2id_dict[e2]) + "\t" + str(rel2id[rel]) + "\n")
    
    aser_core_graph.close()
    aser_graph.close()
    
    aser_large = nx.MultiGraph()
    nx.read_edgelist(data_dir + "graph/aser_core_graph.dat", create_using=aser_large, nodetype=int, data=(('rel', int),))

    print(aser_large.number_of_nodes(), aser_large.number_of_edges())
    # 2,340,259 7,929,247
    nx.write_gpickle(aser_large, data_dir + "graph/aser_graph.nx")

def load_kg(data_dir):
    print("loading cpnet....")
    data_path = os.path.join(data_dir, 'graph/aser_graph.nx')
    kg_full = nx.read_gpickle(data_path)

    # kg_simple: directed graphs with binary relation (connected or non)
    kg_simple = nx.DiGraph()
    for u, v, data in kg_full.edges(data=True):
        kg_simple.add_edge(u, v)
    
    print(kg_simple.number_of_nodes(), kg_simple.number_of_edges())
    print(kg_full.number_of_nodes(), kg_full.number_of_edges())

    return kg_full, kg_simple

def path2str(path, id2rel, rel2id, eid2aid, aid2word):

    str2w = []
    _idx = 0
    ent = aid2word[eid2aid[path[_idx]]]
    str2w.append(ent)
    _idx += 1
    while _idx < len(path):
        rel = id2rel[path[_idx]]
        _idx += 1
        ent = aid2word[eid2aid[path[_idx]]]
        _idx += 1
        str2w.append(rel)
        str2w.append(ent)

    str2w = ' || '.join(str2w) + '\n'
    return str2w

def random_walk(start_node, kg_full, kg_simple, max_len=3):

    # random walk functions are referred from:
    # https://github.com/wangpf3/Commonsense-Path-Generator

    edges_before_t_iter = 0
    # while True:
    #     curr_node = random.randint(0, nr_nodes-1) 
    #     if curr_node in kg_simple:
    #         break
    curr_node = start_node
    num_sampled_nodes = 1
    path = [curr_node]
    node_visited = set()
    relation_visited = set()
    node_visited.add(curr_node)
    while num_sampled_nodes != max_len:
        edges = [n for n in kg_simple[curr_node]]
        #print(edges)
        if len(edges) == 0:
            #print("the node has no adjancent")
            break
        iteration_node = 0
        flag_valid = False
        while True:
            index_of_edge = random.randint(0, len(edges) - 1)
            chosen_node = edges[index_of_edge]
            if not chosen_node in node_visited:
                rel_list = kg_full[curr_node][chosen_node]
                rel_list = list(set([rel_list[item]['rel'] for item in rel_list \
                                    if rel_list[item]['rel']!=14]))
                iteration_rel = 0
                while True:
                    index_of_rel = np.random.choice(len(rel_list), 1)[0]
                    chosen_rel = kg_full[curr_node][chosen_node][index_of_rel]['rel']
                    if chosen_rel not in relation_visited:
                        flag_valid = True
                        break
                    else:
                        iteration_rel += 1
                        if iteration_rel >= 3:
                            break
                if flag_valid:
                    break
                else:
                    iteration_node += 1
                    if iteration_node >= 3:
                        return []
            else:
                iteration_node += 1
                if iteration_node >= 3:
                    return []
        node_visited.add(chosen_node)
        relation_visited.add(chosen_rel % 20)
        path.append(chosen_rel)
        path.append(chosen_node)

        curr_node = chosen_node
        num_sampled_nodes += 1
    return path 

if __name__ == "__main__":
    data_dir = "/data/aser/core/"
    #preprocess(data_dir)
    #save_pickled_graph(data_dir)
    num_paths = [10, 8, 6, 4, 2]
    path_lens = [2, 3, 4, 5, 6] # 1,2,3,4 hop

    ## Comments: May 16th 2021
    ## Need to sample the meta paths
    ## rare neighborhood edges are reasonable in the ASER

    output_path = "/data/aser/core/graph/sampled_path_2.txt"

    nr_nodes = len(kg_full.nodes())
    visited_concept = dict()
    num_visited_concept = len(visited_concept)
    not_visited_idx = []
    for cnpt_idx in range(nr_nodes):
    #if not en_v1[cnpt_idx] in visited_concept:
        not_visited_idx.append(cnpt_idx)
    print('not visited: {}'.format(len(not_visited_idx)))
   
    print(num_paths)
    with open(output_path, 'w') as fw:
        for curr_node in tqdm(not_visited_idx, desc='generating paths'):
            if not curr_node in kg_simple:
                continue 
            visited_path = set()
            for _id, _len in enumerate(path_lens):            
                for pid in range(num_paths[_id]):
                    num_try = 0
                    while True:
                    path = random_walk(curr_node, kg_full, kg_simple, _len)
                        if len(path) > 0:
                        str2w = path2str(path, id2rel, rel2id, eid2aid, aid2word)
                        if str2w not in visited_path:
                            fw.write(str2w)
                            visited_path.add(str2w)
                            break
                    num_try += 1
                    if num_try >10:
                        break

fw.close()
