#include"cut.h"

int branchdecomp(int nodes, int edges, int *end1, int *end2, int &width,
  int &bnodes, int &bedges, int *&bend1, int *&bend2, int *&nu) {

  graph g, /*l,*/ *u = nullptr;
  bgraph b;
  int comp;

  create(nodes, edges, end1, end2, g);
  //std::cerr<<"created\n";
  bcreate(b);
  //delete []end1;
  //delete []end2;

  components(g, comp, u);
  //std::cerr<<comp<<" comps\n";
  if (comp == 1) {
    bwcomps(g, g, b);
  } else {
    for (int i = 0; i < comp; i++) {
      bwcomps(g, u[i], b);
      freegraph(u[i]);
    }
    delete[] u;
    int e = 0;
    for (int i = 0; i < g.edges; i++) {
      if (g.nlist[g.elist[i].end1].token == 0) {
        e = i;
        break;
      }
    }
    for (int i = 1; i < comp; i++) {
      for (int j = 0; j < g.edges; j++) {
        if (g.nlist[g.elist[j].end1].token == i) {
          //std::cerr<<e<<" and "<<j<<"\n";
          blink(e, j, g, b);
          break;
        }
      }
    }
  }

  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].color = 0;
  }
  if (b.edges != b.nodes - 1)std::cerr << b.nodes << " ERROR on forming tree " << b.edges << "\n";
  //std::cerr<<"hello\n";
  bnode *it = nullptr;
  for (bnode *n = b.nlist; n; n = n->next) {
    if (n->degree == 3) {
      it = n;
      break;
    }
  }
  if (it == nullptr) it = b.nlist;
  postdfs(it, b);
  //for(bedge *e=b.elist; e; e=e->next){
  //std::cerr<<e->end1<<" & "<<e->end2<<" b's edges\n";
  //}
  //std::cerr<<"hello\n";
  width = b.width;
  for (bqueue *n = b.head; n->next; n = n->next) {
    width = b.width;
    //std::cerr<<n<<" n\n";
    //if(n != nullptr){
    //std::cerr<<n->bv<<" n->bv\n";
    //if(n->bv != nullptr){
    //std::cerr<<n->bv->index<<" bnode\n";
    // }
    //}
    bwidth(n->bv, b, g);
    /*if(b.width != width){
     //std::cerr<<b.width<<" new width\n";
     for(bqueue *r=b.head; r!=n->next; r=r->next){
     if(r->bv->degree==1){
     int need=r->bv->arcs->index;
     //std::cerr<<g.elist[need].end1<<" and "<<g.elist[need].end2<<" edges\n";
     }
     }
     }*/
  }

  bnodes = b.nodes;
  bedges = b.edges;
  //std::cerr << bnodes << " " << bedges << " b\n";
  bend1 = new int[bedges];
  bend2 = new int[bedges];
  int wk = 0;
  for (bedge *ie = b.elist; ie; ie = ie->next) {
    bend1[wk] = ie->end1;
    bend2[wk] = ie->end2;
    wk++;
  }

  nu = new int[g.edges];

  for (bnode *ib = b.nlist; ib; ib = ib->next) {
    if (ib->arcs != nullptr) {
      nu[ib->arcs->index] = ib->index;
      //std::cerr << ib->arcs->index << " has holder " << ib->index << "\n";
    }
  }
  //std::cout<<"The branchwidth of the graph "<<argv[1]<<" is <= "<<b.width<<"\n";

  freegraph(g);
  freebgraph(b);

  return 0;
}

int main(int argc, char *argv[]) {
  graph g, /*l,*/ *u = nullptr;
  bgraph b;
  int nodes, edges, *end1, *end2, comp;

  std::cin.ignore(5);
  std::cin >> nodes >> edges;
  end1 = new int[edges];
  end2 = new int[edges];

  for (int i = 0; i < edges; i++) {
    std::cin >> end1[i] >> end2[i];
    end1[i]--;
    end2[i]--;
    // //std::cerr << end1[i] << " " << end2[i] << "\n";
  }

  //std::cerr << nodes << " nodes and edges " << edges << "\n";
  create(nodes, edges, end1, end2, g);
  //std::cerr << "Created graph\n";
  bcreate(b);
  delete[] end1;
  delete[] end2;
  /*
  int c=0;
  for(int i=0; i<g.edges; i++){
    for(int j=i+1; j<g.edges; j++){
      if(g.elist[i].end1==g.elist[j].end1 || g.elist[i].end1==g.elist[j].end2
     || g.elist[i].end2==g.elist[j].end1
     || g.elist[i].end2==g.elist[j].end2){
    c++;
    if(i==1){
    //std::cerr<<j<<" and 1 share an end\n";
    }
      }
    }
  }
  end1=new int[c];
  end2=new int[c];
  int cc=c;
  c=0;
  for(int i=0; i<g.edges; i++){
    for(int j=i+1; j<g.edges; j++){
      if(g.elist[i].end1==g.elist[j].end1 || g.elist[i].end1==g.elist[j].end2
     || g.elist[i].end2==g.elist[j].end1
     || g.elist[i].end2==g.elist[j].end2){
    end1[c]=i;
    end2[c]=j;
    c++;
      }
    }
  }
  //std::cerr<<g.edges<<" "<<cc<<"\n";
  for(int i=0;i<cc; i++){
    //std::cerr<<end1[i]<<" "<<end2[i]<<" "<<1<<"\n";
  }

  create(g.edges, cc, end1, end2, l);
  delete []end1;
  delete []end2;
  */

  center(g);
  /*
   for(int i=0; i<g.edges; i++){
     for(int j=0; j<g.edges; j++){
       if( i != j  &&(g.elist[i].end1==g.elist[j].end1
               || g.elist[i].end1==g.elist[j].end2
               || g.elist[i].end2==g.elist[j].end1
               || g.elist[i].end2==g.elist[j].end2)){
     g.elist[i].tree++;
       }
     }
   }
   //std::cerr<<"[";
   for(int i=0; i<g.edges; i++){
     for(int j=0; j<g.edges; j++){
       if(i==j){
     //std::cerr<<g.elist[i].tree<<" ";
       }
       else if(g.elist[i].end1==g.elist[j].end1
           || g.elist[i].end1==g.elist[j].end2
           || g.elist[i].end2==g.elist[j].end1
           || g.elist[i].end2==g.elist[j].end2){
     //std::cerr<<"-1 ";
       }
       else{
     //std::cerr<<"0 ";
       }
     }
     //std::cerr<<";\n";
   }
   //std::cerr<<"]\n";
   */
  components(g, comp, u);
  if (comp == 1) {
    bwcomps(g, g, b);
  } else {
    for (int i = 0; i < comp; i++) {
      bwcomps(g, u[i], b);
      freegraph(u[i]);
    }
    delete[] u;
    int e = 0;
    for (int i = 0; i < g.edges; i++) {
      if (g.nlist[g.elist[i].end1].token == 0) {
        e = i;
        break;
      }
    }
    for (int i = 1; i < comp; i++) {
      for (int j = 0; j < g.edges; j++) {
        if (g.nlist[g.elist[j].end1].token == i) {
          // //std::cerr << e << " and " << j << "\n";
          blink(e, j, g, b);
          break;
        }
      }
    }
  }

  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].color = 0;
  }
  if (b.edges != b.nodes - 1 || b.nodes != 2 *g.edges - 2) {
    std::cerr << b.nodes << " ERROR on forming tree " << b.edges << "\n";
  }

  bnode *it = nullptr;
  for (bnode *n = b.nlist; n; n = n->next) {
    if (n->degree == 3) {
      it = n;
      break;
    }
  }
  if (it == nullptr) it = b.nlist;
  postdfs(it, b);
  /*
  for (bedge *e = b.elist; e; e = e->next) {
    std::cerr << e->end1 << " & " << e->end2 << " b's edges\n";
  }
  */

  //int width=b.width;
  for (bqueue *n = b.head; n->next; n = n->next) {
    //width=b.width;
    //std::cerr << n << " n\n";
    if (n != nullptr) {
      //std::cerr << n->bv << " n->bv\n";
      if (n->bv != nullptr) {
        //std::cerr << n->bv->index << " bnode\n";
      }
    }
    bwidth(n->bv, b, g);
    /*if(b.width != width){
      //std::cerr<<b.width<<" new width\n";
      for(bqueue *r=b.head; r!=n->next; r=r->next){
    if(r->bv->degree==1){
      int need=r->bv->arcs->index;
      //std::cerr<<g.elist[need].end1<<" and "<<g.elist[need].end2<<" edges\n";
    }
      }
    }*/
  }

  /*
  //std::cerr<<"hello\n";
  //std::cerr<<"hello\n";
  int *ms=new int[b.width];
  for(int i=0; i<b.width; i++){
    ms[i]=0;
  }
  for(bedge *e=b.elist; e; e=e->next){
    ms[e->order-1]++;
    e->color=0;
  }
  int ct=0;
  int *fill=new int[g.nodes];
  for(int i=0; i<g.nodes; i++){
    g.nlist[i].token=0;
    if(g.nlist[i].degree==0){
      fill[ct]=i;
      ct++;
      g.nlist[i].token=1;
    }
  }
  //std::cerr<<b.head->bv->degree<<" degree\n";
  //std::cerr<<"hello\n";
  for(bqueue *n=b.head; n->next; n=n->next){
    fillin(n->bv, b, g, ct, fill);
  }


  for(int i=0; i<g.nodes; i++){
    g.nlist[i].cut=0;
  }

  bedge *e=it->adj->be;
  bedge *ee=it->adj->next->be;

  for(int i=0; i<e->order; i++){
    g.nlist[e->ms[i]].cut+=e->msdeg[i];
  }

  for(int i=0; i<ee->order; i++){
    g.nlist[ee->ms[i]].cut+=ee->msdeg[i];
  }

  for(int i=0; i<g.nodes; i++){
    if(g.nlist[i].token==0 &&g.nlist[i].cut==g.nlist[i].degree){
      fill[ct]=i;
      g.nlist[i].token=1;
      ct++;
    }
  }

  for(int i=0; i<g.nodes; i++){
    if(g.nlist[i].token==0){
      fill[ct]=i;
      ct++;
    }
  }

  //std::cerr<<"CUTS:\n";
  int mc=0;
  for(int i=0; i<b.width; i++){
    if(ms[i] > 0){
      //std::cerr<<"MS["<<i+1<<"]= "<<ms[i]<<"  ";
      mc++;
    }
    if(mc% 5==0 &&mc !=0){
      //std::cerr<<"\n";
    }
  }
  //std::cerr<<"\n";
  delete []ms;
  //std::cerr<<"FILLIN ORDER:\n";
  for(int i=0; i<g.nodes; i++){
    //std::cerr<<"FILL["<<i+1<<"]= "<<fill[i]<<" ";
    if(i%5 ==0 &&i!=0){
      //std::cerr<<"\n";
    }
  }
  //std::cerr<<"\n";
  delete []fill;
  */

  /*
  std::cout << b.nodes << " " << b.edges << " " << b.width << "\n";
  for (bedge *e = b.elist; e; e = e->next) {
    std::cout << e->end1 << " " << e->end2 << " 1\n";
  }
  
  std::cout << g.nodes << " " << g.edges << "\n";
  for (int i = 0; i < g.edges; i++) {
    std::cout << g.elist[i].end1 << " " << g.elist[i].end2 << " ";
    std::cout << g.elist[i].holder->index << "\n";
  }
  std::cout << "The branchwidth of the graph is <= " << b.width << "\n";
  */

  std::cout << "c Outputting branchwidth " << b.width << "\n";
  std::cout << "s bd " << g.edges << " " << b.nodes << " " << b.width << " " << b.edges << "\n";
  for (int i = 0; i < g.edges; i++) {
    std::cout << "b " << (g.elist[i].holder->index+1) << " " << (i+1) << "\n";
  }
  for (bedge *e = b.elist; e; e = e->next) {
    std::cout << (e->end1+1) << " " << (e->end2+1) << "\n";
  }
  freegraph(g);
  freebgraph(b);

  return 0;
}

void bwcomps(graph &bigg, graph &g, bgraph &b) {
  graph *u;
  int comp;
  //ofstream graphs("graphs", ios::app);

  for (int i = 0; i < g.edges; i++) {
    g.elist[i].tree = 0;
  }
  bicomps(g, comp, u);
  //std::cerr<<comp<<" bicomp\n";
  if (comp == 1) {
    //graphs<<g.nodes<<" "<<g.edges<<"\n";
    //for(int j=0; j<g.edges; j++){
    //graphs<<g.elist[j].end1<<" "<<g.elist[j].end2<<" 1\n";
    //}
    //graphs<<"\n";
    bdecomp(bigg, g, b);
    bigg.width = max(bigg.width, g.width);
  } else {
    for (int i = 0; i < comp; i++) {
      //graphs<<u[i].nodes<<" "<<u[i].edges<<"\n";
      //for(int j=0; j<u[i].edges; j++){
      //graphs<<u[i].elist[j].end1<<" "<<u[i].elist[j].end2<<" 1\n";
      //}
      //graphs<<"\n";
      bdecomp(bigg, u[i], b);
      bigg.width = max(bigg.width, u[i].width);
      freegraph(u[i]);
    }
    delete[] u;

    for (int i = 0; i < g.edges; i++) {
      g.elist[i].path = 0;
    }
    for (int i = 0; i < g.nodes; i++) {
      if (g.nlist[i].art >= 1) {
        for (int j = 1; j < g.nlist[i].degree; j++) {

          if (g.elist[g.nlist[i].adj[j]].tree !=
            g.elist[g.nlist[i].adj[0]].tree &&
            g.elist[g.nlist[i].adj[j]].path == 0) {
            //std::cerr<<i<<" art node\n";
            //std::cerr<<g.elist[g.nlist[i].adj[j]].index<<" with bcomp "<<g.elist[g.nlist[i].adj[j]].tree<<"\n";
            //std::cerr<<g.elist[g.nlist[i].adj[0]].index<<" with bcomp "<<g.elist[g.nlist[i].adj[0]].tree<<"\n";
            blink(g.elist[g.nlist[i].adj[j]].index,
              g.elist[g.nlist[i].adj[0]].index, bigg, b);

            for (int k = j + 1; k < g.nlist[i].degree; k++) {

              if (g.elist[g.nlist[i].adj[k]].tree ==
                g.elist[g.nlist[i].adj[j]].tree) {

                g.elist[g.nlist[i].adj[k]].path = 1;
              }
            }
          }
          g.elist[g.nlist[i].adj[j]].path = 0;
        }
      }
    }

  }
}

void bdecomp(graph &bigg, graph &g, bgraph &b) {
  int cuts = -1, *cutx = nullptr, *side1 = nullptr, *side2 = nullptr, es1 = 0, es2 = 0;
  //std::cerr<<"hello\n";

  bconnect(g, b, bigg);

  if (g.edges > 1) {
    if (g.edges == (int)(g.nodes *(g.nodes - 1) / 2)) {
      //std::cerr<<"Case 1\n";
      cuts = 2;
      es1 = 1;
      es2 = g.edges - es1;
      cutx = new int[cuts];
      side1 = new int[es1];
      side2 = new int[es2];
      side1[0] = 0;
      cutx[0] = g.elist[0].end1;
      g.nlist[cutx[0]].cut = 1;
      cutx[1] = g.elist[0].end2;
      g.nlist[cutx[1]].cut = 1;
      for (int i = 1; i < g.edges; i++) {
        side2[i - 1] = i;
      }
    } else {
      /*int v=-1;
      for(int i=0; i<g.nodes; i++){
	if(g.nlist[i].degree==2){
	  v=i;
	  break;
	}
      }
      if( v>=0){
	cuts=2;
	es1=2;
	es2=g.edges-2;
	cutx=new int[cuts];
	side1=new int[es1];
	side2=new int[es2];
	int c=0, cc=0;
	for(int i=0; i<g.edges; i++){
	  if(g.elist[i].end1==v){
	    g.nlist[g.elist[i].end2].cut=1;
	    cutx[c]=g.elist[i].end2;
	    side1[c]=i;
	    c++;
	  }
	  else if( g.elist[i].end2==v){
	    g.nlist[g.elist[i].end1].cut=1;
	    cutx[c]=g.elist[i].end1;
	    side1[c]=i;
	    c++;
	  }
	  else{
	    side2[cc]=i;
	    cc++;
	  }
	}
      }
      else{
      */
      findcut3(g, cuts, cutx, es1, side1, es2, side2);
      //}
    }
    //showmecut(g, cuts, es1, es2, cutx, side1, side2);
    split(bigg, g, cuts, cutx, es1, side1, es2, side2, g.bn, b);
  }
}

void create(int nodes, int edges, int *end1, int *end2, graph &g) { //Note: end1 has to min of the two
  g.width = 0;
  g.nodes = nodes;
  g.edges = edges;
  g.nlist = new node[nodes];
  g.elist = new edge[edges];

  //std::cerr<<g.nodes<<" nodes and edges "<<g.edges<<"\n";
  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].degree = 0;
    g.nlist[i].x = 0;
    g.nlist[i].cut = 0;
    g.nlist[i].tree = 0;
    g.nlist[i].index = i;
    g.nlist[i].number = 0;
    g.nlist[i].lowpt = 0;
    g.nlist[i].art = 0;
    g.nlist[i].color = -1;
    g.nlist[i].father = nullptr;
    g.nlist[i].forward = nullptr;
    g.nlist[i].token = 0;
    g.nlist[i].back = nullptr;
    g.nlist[i].adj = nullptr;
  }

  for (int i = 0; i < g.edges; i++) {
    if (end1[i] >= g.nodes) {
      //std::cerr << end1[i] << " end1\n";
    }
    if (end2[i] >= g.nodes) {
      //std::cerr << end2[i] << " end2\n";
    }
    g.elist[i].end1 = end1[i];
    g.nlist[g.elist[i].end1].degree++;
    g.elist[i].end2 = end2[i];
    if (end1[i] != end2[i]) {
      g.nlist[g.elist[i].end2].degree++;
    }
    g.elist[i].tree = 0;
    g.elist[i].index = i;
    g.elist[i].path = 0;
    g.elist[i].wk = 0;
    g.elist[i].st = 0;
    g.elist[i].father = nullptr;
    g.elist[i].tail = nullptr;
    g.elist[i].holder = nullptr;
  }

  for (int i = 0; i < g.edges; i++) {
    int end1 = g.elist[i].end1;
    int end2 = g.elist[i].end2;
    if (g.nlist[end1].adj == nullptr) {
      g.nlist[end1].adj = new int[g.nlist[end1].degree];
    }
    if (g.nlist[end2].adj == nullptr) {
      g.nlist[end2].adj = new int[g.nlist[end2].degree];
    }
    g.nlist[end1].adj[g.nlist[end1].token] = i;
    g.nlist[end1].token++;
    if (end1 != end2) {
      g.nlist[end2].adj[g.nlist[end2].token] = i;
      g.nlist[end2].token++;
    }
  }

  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].token = 0;
  }
}

void freegraph(graph &g) {
  //std::cerr<<"hello\n";
  if (g.nodes) {
    for (int i = 0; i < g.nodes; i++) {
      if (g.nlist[i].adj) {
        delete[] g.nlist[i].adj;
      }
    }
  }
  //std::cerr<<"hello\n";
  g.nodes = 0;

  if (g.nlist) delete[] g.nlist;
  if (g.elist) delete[] g.elist;
  //std::cerr<<"freegraph\n";
}

void initialize(graph &g) {

  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].x = 0;
    g.nlist[i].tree = 0;
    g.nlist[i].number = -1;
    g.nlist[i].lowpt = -1;
    g.nlist[i].art = 0;
    g.nlist[i].color = -1;
    g.nlist[i].father = nullptr;
    g.nlist[i].forward = nullptr;
    g.nlist[i].back = nullptr;
  }

  for (int i = 0; i < g.edges; i++) {
    g.elist[i].tree = -1;
    g.elist[i].path = 0;
    g.elist[i].wk = 0;
    g.elist[i].st = 0;
    g.elist[i].father = nullptr;
    g.elist[i].tail = nullptr;
  }
}

void onecut(graph &g, int &cuts, int *&cutx, int &es1, int *&side1, int &es2,
  int *&side2) {
  int e = -1, end = -1, n = 0;
  int comp = 0;
  //std::cerr<<"new graph with "<<g.edges<<" edges\n";
  /*for(int i=0; i<g.edges; i++){
    //std::cerr<<g.nlist[g.elist[i].end1].index<<" "<<g.nlist[g.elist[i].end2].index;
    //std::cerr<<" g's edges\n";
  }
  for(int i=0; i<g.nodes; i++){
    g.nlist[i].number=0;
  }
  for(int i=0; i<g.nodes; i++){
    if(g.nlist[i].number==0){
      comp++;
      dfs(g, comp, i);
    }
  }
  //std::cerr<<comp<<" onecut comp\n";
  */
  //This finds separations <= cnodes this includes star separations
  //and the new critiera separations  
  int ee = -1;
  for (int i = 0; i < g.edges; i++) {
    g.elist[i].parent = i;
    g.elist[i].mark = 0;
  }

  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].cut != 1) {
      for (int j = 1; j < g.nlist[i].degree; j++) {
        eunionn(g.nlist[i].adj[0], g.nlist[i].adj[j], g.elist);
      }
    }
  }
  comp = 0;
  for (int i = 0; i < g.edges; i++) {
    if (efind(i, g.elist) == i) {
      comp++;
      ee = i;
    }
  }
  //std::cerr<<comp<<" onecut comps\n";
  if (comp > 1) {
    //std::cerr<<comp<<" cutnode comps\n";
    int count = 0;
    for (int i = 0; i < g.edges; i++) {
      if (efind(i, g.elist) == ee) {
        count++;
      }
    }
    es1 = count;
    es2 = g.edges - es1;
    side1 = new int[es1];
    side2 = new int[es2];
    int ecount = 0;
    count = 0;
    for (int i = 0; i < g.edges; i++) {
      if (efind(i, g.elist) == ee) {
        side1[count] = i;
        count++;
      } else {
        side2[ecount] = i;
        ecount++;
      }
    }
    cuts = 0;
    cutx = nullptr;
  } else {
    for (int i = 0; i < g.nodes; i++) {
      if (g.nlist[i].cut == 1) {
        if (g.nlist[i].degree == 1) {
          e = g.nlist[i].adj[0];
          end = g.elist[e].end1 + g.elist[e].end2 - i;
          break;
        }
        n++;
      }
    }

    if (e >= 0) {
      //std::cerr<<g.nlist[g.elist[e].end1].index<<" onecut ";
      //std::cerr<<g.nlist[g.elist[e].end2].index<<"\n";
      es1 = 1;
      cuts = 1;
      es2 = g.edges - 1;
      cutx = new int[cuts];
      side1 = new int[es1];
      side2 = new int[es2];
      cutx[0] = end;
      side1[0] = e;
      g.nlist[end].cut = 1;
      n = 0;
      for (int i = 0; i < g.edges; i++) {
        if (i != e) {
          side2[n] = i;
          n++;
        }
      }
    } else {
      /*
            //std::cerr<<"look for node adj to only cut nodes\n";
            int count=0;
            n=-1;
            
            for(int i=0; i<g.nodes; i++){
      	g.nlist[i].color=0;
      	if(g.nlist[i].cut!=1){
      	  g.nlist[i].color=1;
      	}
            }
            for(int i=0; i<g.nodes; i++){
      	if(g.nlist[i].color==1){
      	  count=0;
      	  for(int j=0; j<g.nlist[i].degree; j++){
      	    int e=g.nlist[i].adj[j];
      	    int other=g.elist[e].end1 + g.elist[e].end2 - i;
      	    if(g.nlist[other].cut==1){
      	      count++;
      	    }
      	    else{
      	      g.nlist[other].color=0;
      	      //break;
      	    }
      	  }
      	  if(n<0 &&count==g.nlist[i].degree){
      	    n=i;
      	    break;
      	  }
      	}
            }
            
            for(int i=0; i<g.edges; i++){
      	if(g.nlist[g.elist[i].end1].cut==1 &&g.nlist[g.elist[i].end2].cut!=1){
      	  count=1;
      	  int v=g.elist[i].end2;
      	  for(int j=0; j<g.nlist[v].degree; j++){
      	    if(g.nlist[v].adj[j] > i){
      	      int e=g.nlist[v].adj[j];
      	      int other=g.elist[e].end1 + g.elist[e].end2 -v;
      	      if(g.nlist[other].cut==1){
      		count++;
      	      }
      	    }
      	  }
      	  if(n<0 &&count==g.nlist[v].degree){
      	    n=v;
      	    break;
      	  }
      	}
      	if(g.nlist[g.elist[i].end2].cut==1 &&g.nlist[g.elist[i].end1].cut!=1){
      	  count=1;
      	  int v=g.elist[i].end1;
      	  for(int j=0; j<g.nlist[v].degree; j++){
      	    if(g.nlist[v].adj[j] > i){
      	      int e=g.nlist[v].adj[j];
      	      int other=g.elist[e].end1 + g.elist[e].end2 -v;
      	      if(g.nlist[other].cut==1){
      		count++;
      	      }
      	    }
      	  }
      	  if(n<0 &&count==g.nlist[v].degree){
      	    n=v;
      	    break;
      	  }
      	}
            }
            if(n>=0){
      	//std::cerr<<"found it "<<g.nlist[n].index<<" n\n";
      	if(g.nlist[n].degree != g.edges){
      	  cuts=g.nlist[n].degree;
      	  es1=cuts;
      	  es2=g.edges-cuts;
      	  cutx=new int[cuts];
      	  side1=new int[es1];
      	  side2=new int[es2];
      	  
      	  count=0, e=0;
      	  for(int i=0; i<g.edges; i++){
      	    if(g.elist[i].end1==n || g.elist[i].end2==n){
      	      int w=g.elist[i].end1 + g.elist[i].end2 -n;
      	      cutx[count]=w;
      	      g.nlist[w].cut=1;
      	      side1[count]=i;
      	      count++;
      	    }
      	    else{
      	      side2[e]=i;
      	      e++;
      	    }
      	  }
      	}
      	else{
      	  //std::cerr<<" the graph is a star\n";
      	  cuts=g.nlist[n].degree;
      	  es1=cuts-1;
      	  es2=1;
      	  cutx=new int[cuts];
      	  side1=new int[es1];
      	  side2=new int[es2];
      	  
      	  for(int i=0; i<g.nlist[n].degree-1; i++){
      	    int k=g.nlist[n].adj[i];
      	    int w=g.elist[k].end1 + g.elist[k].end2 -n;
      	    side1[i]=k;
      	    cutx[i]=w;
      	  }
      	  e=g.nlist[n].adj[g.nlist[n].degree-1];
      	  side2[0]=e;
      	  cutx[g.nlist[n].degree-1]=g.elist[e].end1 + g.elist[e].end2 - n;
      	}
            }
            else{
      	
      	for(int i=0; i<g.edges; i++){
      	  //std::cerr<<g.elist[i].end1<<" & "<<g.elist[i].end2<<"\n";
      	}
      	for(int i=0; i<g.nodes; i++){
      	  if(g.nlist[i].cut==1){
      	    //std::cerr<<i<<" is a cut node\n";
      	  }
      	}
      	int e=-1;
      	int count=0;
      	int c=0;
      	for(int i=0; i<g.nodes; i++){
      	  g.nlist[i].color=0;
      	  if(g.nlist[i].cut!=1){
      	    g.nlist[i].color=1;
      	  }
      	}
      	for(int i=0; i<g.edges; i++){
      	  if(g.nlist[g.elist[i].end1].color==1 
      	     &&g.nlist[g.elist[i].end2].color==1){ 
      	    count=0;
      	    c=0;
      	    int v=g.elist[i].end1;
      	    int w=g.elist[i].end2;
      	    for(int j=0; j<g.nlist[v].degree; j++){
      	      int other=g.elist[g.nlist[v].adj[j]].end1 +g.elist[g.nlist[v].adj[j]].end2 - v;
      	      if(g.nlist[other].cut==1){
      		count++;
      	      }
      	      else{
      		g.nlist[other].color=0;
      		break;
      	      }
      	    }
      	    for(int j=0; j<g.nlist[w].degree; j++){
      	      int other=g.elist[g.nlist[w].adj[j]].end1 +g.elist[g.nlist[w].adj[j]].end2 - w;
      	      if(g.nlist[other].cut==1){
      		c++;
      	      }
      	      else{
      		g.nlist[other].color=0;
      		//break;
      	      }
      	    }
      	    if(count== g.nlist[v].degree-1 &&c== g.nlist[w].degree-1){
      	      e=i;
      	      //break;
      	    }	  
      	  }
      	}
      	if(e>=0){
      	  //std::cerr<<"new critiera\n";
      	  int v=g.elist[e].end1;
      	  int w=g.elist[e].end2;
      	  es1=g.nlist[v].degree + g.nlist[w].degree -1;
      	  es2=g.edges-es1;
      	  side1=new int[es1];
      	  side2=new int[es2];
      	  for(int i=0; i<g.nodes; i++){
      	    g.nlist[i].color=0;
      	  }
      	  count=0;
      	  int count1=0;
      	  for(int i=0; i<g.edges; i++){
      	    if(g.elist[i].end1!=v &&g.elist[i].end2!=v 
      	       &&g.elist[i].end1 !=w &&g.elist[i].end2 != w){
      	      side2[count1]=i;
      	      count1++;
      	    }
      	    else{
      	      side1[count]=i;
      	      count++;
      	      if(g.nlist[g.elist[i].end1].cut==1){
      		g.nlist[g.elist[i].end1].color=1;
      	      }
      	      if(g.nlist[g.elist[i].end2].cut==1){
      		g.nlist[g.elist[i].end2].color=1;
      	      }
      	    }
      	  }
      	  count=0;
      	  for(int i=0; i<g.nodes; i++){
      	    if(g.nlist[i].color==1){
      	      count++;
      	    }
      	  }
      	  cuts=count;
      	  cutx=new int[cuts];
      	  count=0;
      	  for(int i=0; i<g.nodes; i++){
      	    if(g.nlist[i].color==1){
      	      cutx[count]=i;
      	      count++;
      	    }
      	  }	  
      	}
      	else{*/
      //std::cerr<<"findcut3\n";
      findcut3(g, cuts, cutx, es1, side1, es2, side2);
      //}
      //}
    }
  }
  //showmecut(g, cuts, es1, es2, cutx, side1, side2);
  return;
}

//findcut using cuts between nodes whose distance is the diameter
void findcut2(graph &g, int &cuts, int *&cutx, int &es1, int *&side1, int &es2,
  int *&side2) {
  int ti = -1, tj = -1, tcut = 0, tx, share, oshare = 0;
  short *p, ** a;
  int limit, diam = 0;
  int cnodes = 0;

  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].cut == 1) {
      //std::cerr<<g.nlist[i].index<<" is a cut node\n";
      cnodes++;
    }
  }

  int ok = 0;
  cuts = -1;
  limit = (int)(g.nodes *(g.nodes + 1) / 2);
  p = new short[limit];
  a = new short *[g.nodes];
  for (int i = 0, j = 0; i < g.nodes; i++, j += i) {
    a[i] = &p[j];
    if (j > 0) {
      p[j - 1] = 0;
    }
  }
  for (int i = 0; i < g.nodes - 1; i++) {
    bfs(i, diam, a, g);
  }

  for (int i = 0; i < g.nodes; i++) {
    for (int j = i + 1; j < g.nodes; j++) {
      if ((int) a[j][i] == diam) {
        ok = cut(g, i, j, 0, tcut, cutx, es1, side1, es2, side2);
        tx = 0;
        share = 0;
        for (int k = 0; k < g.nodes; k++) {
          if (g.nlist[k].cut == 1) {
            if (g.nlist[k].x == 2) {
              //std::cerr<<g.nlist[k].index<<" count tx\n";
              tx++;
            }
            if (g.nlist[k].x == 1) {
              //std::cerr<<g.nlist[k].index<<" count share\n";
              share++;
            }
          }
        }
        //std::cerr<<g.nlist[i].index<<" i\n";
        //std::cerr<<g.nlist[j].index<<" j\n";
        //std::cerr<<tx<<" tx "<<share<<" share "<<cnodes-tx<<" cnodes-tx\n";
        //y=max(tx + share, cnodes-tx);
        if (ok > 0 &&(cuts < 0 ||
            (share > oshare &&tcut < cuts) ||
            (share == oshare &&tcut < cuts))) {
          ti = i;
          tj = j;
          cuts = tcut;
          oshare = share;
        }
      }
    }
  }
  delete[] p;
  delete[] a;
  cut(g, ti, tj, 1, cuts, cutx, es1, side1, es2, side2);
  //std::cerr<<cuts<<" cuts\n";
  //std::cerr<<g.nlist[ti].index<<" ti\n";
  //std::cerr<<g.nlist[tj].index<<" tj\n";
  if (ti < 0 || tj < 0) {
    //std::cerr << cuts << " cuts\n";
    //std::cerr << ti << " ti\n";
    //std::cerr << tj << " tj\n";
    //std::cerr << "ti or tj is less than zero\n";
    for (int i = 0; i < g.edges; i++) {
      //std::cerr << g.elist[i].end1 << " & " << g.elist[i].end2 << " edges\n";
    }
    for (int i = 0; i < g.nodes; i++) {
      if (g.nlist[i].cut == 1) {
        //std::cerr << i << " is a cut node\n";
      }
    }
    exit(-1);
  }

  //showmecut(g, cuts, es1, es2, cutx, side1, side2);  

}

//findcut using the existing cut nodes
void findcut1(graph &g, int &cuts, int *&cutx, int &es1, int *&side1, int &es2,
  int *&side2) {
  int ti = -1, tj = -1, tcut = 0, tx, share, oshare = 0;
  int cnodes = 0, *cn = nullptr;

  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].cut == 1) {
      cnodes++;
    }
  }
  //std::cerr << cnodes << " cnodes\n";
  if (cnodes) {
    //std::cerr<<g.nodes<<" graph nodes\n";
    //std::cerr<<g.edges<<" graph edges\n";
    cn = new int[cnodes];
    cnodes = 0;
    for (int i = 0; i < g.nodes; i++) {
      if (g.nlist[i].cut == 1) {
        cn[cnodes] = i;
        cnodes++;
      }
    }
    int ok = 0;
    cuts = -1;
    for (int i = 0; i < cnodes - 1; i++) {
      for (int j = i + 1; j < cnodes; j++) {
        ok = cut(g, cn[i], cn[j], 0, tcut, cutx, es1, side1, es2, side2);
        tx = 0;
        share = 0;
        for (int k = 0; k < g.nodes; k++) {
          if (g.nlist[k].cut == 1) {
            if (g.nlist[k].x == 2) {
              tx++;
            }
            if (g.nlist[k].x == 1) {
              share++;
            }
          }
        }
        //y=max(tx + share, cnodes-tx);
        if (ok > 0 &&(cuts < 0 || share - tcut > oshare - cuts)) {
          //|| (tcut - share + y) <(cuts - oshare + x))){
          ti = cn[i];
          tj = cn[j];
          cuts = tcut;
          oshare = share;
        }
      }
    }

    cut(g, ti, tj, 1, cuts, cutx, es1, side1, es2, side2);
    //std::cerr<<cuts<<" cuts\n";
    //std::cerr<<ti<<" ti\n";
    //std::cerr<<tj<<" tj\n";
    //std::cerr<<es1<<" side1 side2 "<<es2<<"\n";
    if (cn) delete[] cn;
    if (ti < 0 || tj < 0) {
      //std::cerr << cuts << " cuts\n";
      //std::cerr << ti << " ti\n";
      //std::cerr << tj << " tj\n";
      //std::cerr << "ti or tj is less than zero\n";
      for (int i = 0; i < g.edges; i++) {
        //std::cerr << g.elist[i].end1 << " & " << g.elist[i].end2 << " edges\n";
      }
      for (int i = 0; i < g.nodes; i++) {
        if (g.nlist[i].cut == 1) {
          //std::cerr << i << " is a cut node\n";
        }
      }
      exit(-1);
    }

    //showmecut(g, cuts, es1, es2, cutx, side1, side2);
  } else {
    findcut2(g, cuts, cutx, es1, side1, es2, side2);
  }

}

void showmecut(graph &g, int cuts, int es1, int es2, int *cutx, int *side1,
  int *side2) {
  if (es1 < es2) {
    //std::cerr << es1 << " es1\n";
    for (int i = 0; i < es1; i++) {
      //std::cerr << g.nlist[g.elist[side1[i]].end1].index << " & ";
      //std::cerr << g.nlist[g.elist[side1[i]].end2].index << " the other side\n";
    }
  } else {
    //std::cerr << es2 << " es2\n";
    for (int i = 0; i < es2; i++) {
      //std::cerr << g.nlist[g.elist[side2[i]].end1].index << " & ";
      //std::cerr << g.nlist[g.elist[side2[i]].end2].index << " the other side\n";
    }
  }
  //std::cerr << es1 << " es1\n";
  //std::cerr << es2 << " es2\n";
  //std::cerr << cuts << " cuts\n";
  if (cuts) {
    for (int i = 0; i < cuts; i++) {
      //std::cerr << g.nlist[cutx[i]].index << " the cut\n";
    }
  }

}

int cut(graph &g, int source, int sink, int opt, int &cut, int *&X, int &es1,
  int *&side1, int &es2, int *&side2) // Menger's Thm
{

  int j = 0, count = 0, ok = 1, w;
  //g.initial();
  initialize(g);

  for (int i = 0; i < g.nlist[source].degree; i++) {
    j = g.nlist[source].adj[i];
    w = g.elist[j].end1 + g.elist[j].end2 - source;
    if (w == sink) {
      //std::cerr<<"Invalid combo of source and sink\n";
      //std::cout<<"source and sink are adjacent!!!\n";
      return -1;
    }
  }
  for (int i = 0; i < g.nlist[source].degree; i++) {
    j = g.nlist[source].adj[i];
    if (g.elist[j].path == 0) {
      //std::cout<<"possible path starting at edge "<<j<<"\n";
      //std::cerr<<j<<" edge j\n";
      //std::cerr<<g.elist[j].end1<<" and "<<g.elist[j].end2<<" edge\n";
      //std::cerr<<source<<" the source\n";
      w = g.elist[j].end1 + g.elist[j].end2 - source;
      //std::cerr<<"push on node "<< w<<"\n";
      if (w != source) {
        //std::cerr<<w<<" start with w\n";
        g.elist[j].tail = &g.nlist[source];
        ok = push(w, source, j, source, sink, 1, g.nlist, g.elist);
        cleartree(g.nodes, g.edges, g.nlist, g.elist);
        //std::cerr<<w<<" through with w\n";
        if (ok == 0) {
          count++;
        }
      }
    }
  }
  //std::cerr<<"paths= "<<count<<"\n";

  if (count == g.nlist[source].degree) {
    for (int i = 0; i < g.nlist[source].degree; i++) {
      j = g.nlist[source].adj[i];
      w = g.elist[j].end1 + g.elist[j].end2 - source;
      g.nlist[w].x = 1;
    }
  } else {
    for (int i = 0; i < g.nlist[source].degree; i++) {
      j = g.nlist[source].adj[i];
      w = g.elist[j].end1 + g.elist[j].end2 - source;
      if (g.elist[j].path == 0) {
        //std::cout<<"possible path starting at edge "<<j<<"\n";
        //std::cout<<"push on node "<< w<<"\n";
        g.elist[j].tail = &g.nlist[source];
        push(w, source, j, source, sink, 0, g.nlist, g.elist);
        cleartree(g.nodes, g.edges, g.nlist, g.elist);
      } else {
        g.nlist[w].x = 1;
      }
    }
  }
  g.nlist[source].x = 1;

  ok = 0;
  for (int i = 0; i < g.nodes; i++) {
    ok = 0;
    if (i != source &&i != sink) {
      for (int e = 0; e < g.nlist[i].degree; e++) {
        if (g.elist[g.nlist[i].adj[e]].path > 0) {
          ok++;
        }
      }
      if (ok > 2) {
        std::cerr<<"Error in computing paths for node "<<g.nlist[i].index<<"\n";
      }
    }
  }
  ok = -1;
  for (int i = 0; i < g.nlist[source].degree; i++) {
    j = g.nlist[source].adj[i];
    if (g.elist[j].path != 0) {
      g.elist[j].path = ok;
      w = g.elist[j].end1 + g.elist[j].end2 - source;
      while (w != sink) {
        g.nlist[w].forward->path = ok;
        w = g.nlist[w].forward->end1 + g.nlist[w].forward->end2 - w;
      }
      ok--;
    }
  }
  for (int i = 0; i < g.edges; i++) {
    if (g.elist[i].path > 0) {
      //std::cout << "Error for edge " << i << "\n";
    }
  }
  //std::cout<<"paths= "<<count<<"\n";
  cut = count;
  ok = 0;
  for (int i = 0; i < g.edges; i++) {
    if (g.elist[i].path < 0) {
      // std::cout<<"Edge "<<i<<" is part of path"<<-g.elist[i].path<<"\n";
    }
  }
  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].x == 1) {
      g.nlist[i].x = 2;
      for (int k = 0; k < g.nlist[i].degree; k++) {
        j = g.nlist[i].adj[k];
        w = g.elist[j].end1 + g.elist[j].end2 - i;
        if (g.nlist[w].x == 0) {
          g.nlist[i].x = 1;
          //std::cerr<<g.nlist[i].index<<" is a cut node\n";
        }
      }
    }
  }
  if (opt) {
    X = new int[count];
    for (int i = 0; i < g.nodes; i++) {
      if (g.nlist[i].x == 1) {
        //std::cout<<g.nlist[i].index<<" is in X\n";
        X[ok] = i;
        g.nlist[i].cut = 1;
        ok++;
      }
    }
    count = 0;
    for (int i = 0; i < g.edges; i++) {
      g.elist[i].wk = 0;
      if (g.nlist[g.elist[i].end1].x != 0 &&g.nlist[g.elist[i].end2].x != 0) {
        g.elist[i].wk = 1;
        //std::cerr<<g.elist[i].end1<<" & "<<g.elist[i].end2<<"\n";
        count++;
      }
    }
    es1 = count;
    es2 = g.edges - count;
    side1 = nullptr;
    side2 = nullptr;
    side1 = new int[es1];
    side2 = new int[es2];
    int temp = 0;
    count = 0;
    for (int i = 0; i < g.edges; i++) {
      if (g.elist[i].wk == 0) {
        side2[temp] = i;
        temp++;
      }
      if (g.elist[i].wk == 1) {
        side1[count] = i;
        count++;
      }
    }
  }
  return g.nlist[source].degree;
}

void cleartree(int nodes, int edges, node *nlist, edge *elist) {

  for (int i = 0; i < edges; i++) {
    elist[i].father = nullptr;
    elist[i].tail = nullptr;
  }
  for (int i = 0; i < nodes; i++) {
    nlist[i].tree = 0;
  }

}

//push one unit of flow until stopped or reach sink
int push(int v, int u, int e, int source, int sink, int cut,
  node *nlist, edge *elist) {
  int ok, j = -1;
  int w, k, t;

  elist[e].tail = &nlist[u];
  nlist[u].x = 0;
  nlist[v].tree = 1;
  //std::cerr<<"u = "<<u<<"\n";
  //std::cerr<<"v = "<<v<<"\n";

  if (nlist[v].forward != nullptr &&nlist[v].forward - elist != e) {
    //std::cout<<"condition 1\n";
    j = nlist[v].back - elist;
    if (j < 0) std::cerr << "ERROR in push\n";
    w = elist[j].end1 + elist[j].end2 - v;
    if (elist[j].father == nullptr &&w != source) {
      //std::cout<<"push1 on node "<<w<<"\n";
      elist[j].father = &elist[e];
      ok = push(w, v, j, source, sink, cut, nlist, elist);
      if (ok == 0) {
        return 0;
      }
    }
  } else if (nlist[v].forward != nullptr &&(nlist[v].forward - elist) == e) {
    //std::cout<<"condition 2\n";
    for (int i = 0; i < nlist[v].degree; i++) {
      k = nlist[v].adj[i];
      t = elist[k].end1 + elist[k].end2 - v;
      if (t == sink) {
        elist[j].father = &elist[e];
        augment( &nlist[v], &elist[j], &nlist[source], nlist);
        return 0;
      }
    }
    j = nlist[v].back - elist;
    w = elist[j].end1 + elist[j].end2 - v;
    if (elist[j].father == nullptr &&w != source) {
      //std::cout<<"push2 on node "<<w<<"\n";
      elist[j].father = &elist[e];
      ok = push(w, v, j, source, sink, cut, nlist, elist);
      if (ok == 0) {
        return 0;
      }
    }
    for (int i = 0; i < nlist[v].degree; i++) {
      k = nlist[v].adj[i];
      t = elist[k].end1 + elist[k].end2 - v;
      if (nlist[t].tree == 0 &&k != j &&t != source) {
        //std::cout<<"push2 on node "<<t<<" from "<<v<<"\n";
        elist[k].father = &elist[e];
        ok = push(t, v, k, source, sink, cut, nlist, elist);
        if (ok == 0) {
          return 0;
        }
      }
    }
  } else {
    //std::cout<<"condition 3\n";
    for (int i = 0; i < nlist[v].degree; i++) {
      j = nlist[v].adj[i];
      w = elist[j].end1 + elist[j].end2 - v;
      if (w == sink) {
        elist[j].father = &elist[e];
        augment( &nlist[v], &elist[j], &nlist[source], nlist);
        return 0;
      }
    }
    for (int i = 0; i < nlist[v].degree; i++) {
      j = nlist[v].adj[i];
      w = elist[j].end1 + elist[j].end2 - v;
      if (nlist[w].tree == 0 &&w != source &&elist[j].father == nullptr) {
        //std::cout<<"push3 on node "<<w<<"\n";
        elist[j].father = &elist[e];
        ok = push(w, v, j, source, sink, cut, nlist, elist);
        if (ok == 0) {
          return 0;
        }
      }
    }
  }
  if (cut == 0) {
    nlist[v].x = 1;
    //std::cout<<v<<" is now part of cut\n";
  }

  return 1;
}

void augment(node *v, edge *e, node *source, node *nlist) {
  edge *p;
  int j;

  v->forward = e;
  v->forward->path = 1;
  //std::cout<<v->forward->index<< " is part of a path\n";

  for (p = e->father; p->tail != source; p = p->father) {
    if (p->path == 0) {
      p->path = 1;
      //std::cout<<p->index<<" is part of path\n";
      p->tail->forward = p;
      //std::cout<<p->tail-nlist<<" forward edge is "<<p->index<<"\n";
      j = p->end1 + p->end2 - (p->tail - nlist);
      nlist[j].back = p;
      //std::cout<<j<<" back  edge is "<<p->index<<"\n";
    } else {
      p->path = 0;
      p->tail->back = nullptr;
      j = p->end1 + p->end2 - (p->tail - nlist);
      if (nlist[j].forward->path == 0) {
        nlist[j].forward = nullptr;
      }
      //std::cout<<p->index<<" is not part of a path anymore\n";
    }
  }
  p->path = 1;
  j = p->end1 + p->end2 - (p->tail - nlist);
  nlist[j].back = p;
}

void bfs(int pp, int &bpath, short ** a, graph &d) {
  // color= -1 for white , 0 for gray and 1 for black
  int in = 0, e, w;
  queue *head, *tail;
  for (int i = 0; i < d.nodes; i++) {
    d.nlist[i].color = -1;
  }
  d.nlist[pp].color++;
  queue *q = new queue[1];
  q->elem = pp;
  q->next = nullptr;
  head = q;
  tail = q; in = 1;
  while ( in != 0) {
    int u = head->elem;
    for (int i = 0; i < d.nlist[u].degree; i++) {
      e = d.nlist[u].adj[i];
      w = d.elist[e].end1 + d.elist[e].end2 - u;
      if (d.nlist[w].color == -1) {
        d.nlist[w].color++;
        //a[pp][w]=a[pp][u]+1;
        //a[w][pp]=a[pp][w];
        //if(mval(pp,w,a)==-1 || mval(pp,u,a)+1 < mval(pp,w,a)){
        // inmval(pp,w,mval(pp,u,a)+1,a);
        //if(mval(pp,w,a) > bpath){
        //  bpath=mval(pp,w,a);
        //std::cerr<<pp<<" to "<<w<<" with length "<<bpath<<"\n";
        //}
        a[max(pp, w)][min(pp, w)] = a[max(pp, u)][min(pp, u)] + 1;
        if (a[max(pp, w)][min(pp, w)] > bpath) {
          bpath = a[max(pp, w)][min(pp, w)];
        }
        enqueue(w, tail); in ++;
      }
    }
    queue *p = head;
    head = head->next;
    delete[] p; in --;
    d.nlist[u].color++;
  }
}

void enqueue(int w, queue *&tail) {
  queue *q = new queue[1];

  q->elem = w;
  q->next = nullptr;
  tail->next = q;
  tail = q;
}

void components(graph &g, int &comp, graph *&u) {
  int c = 0;
  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].number = 0;
    g.nlist[i].token = 0;
  }
  //std::cerr<<c<<" c\n";
  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].number == 0) {
      c++;
      dfs(g, c, i);
    }
  }
  comp = 0;
  //std::cerr<<c<<" c\n";
  for (int i = 1; i < c + 1; i++) {
    int ok = 0;
    for (int j = 0; j < g.edges; j++) {
      if (g.nlist[g.elist[j].end1].number == i) {
        if (ok == 0) {
          comp++;
          ok = 1;
        }
        g.nlist[g.elist[j].end1].token = comp - 1;
      }
    }
  }

  if (comp > 1) {
    u = new graph[comp];
    for (int i = 0; i < comp; i++) {
      int num = 0;
      for (int j = 0; j < g.edges; j++) {
        if (g.nlist[g.elist[j].end1].token == i) {
          num++;
        }
      }
      int *nume = new int[num];
      num = 0;
      for (int j = 0; j < g.edges; j++) {
        if (g.nlist[g.elist[j].end1].token == i) {
          nume[num] = j;
          num++;
        }
      }
      splitgraph(num, nume, g, u[i]);
      delete[] nume;
    }
  }
}

void bicomps(graph &g, int &comp, graph *&u) {
  int k = 0;
  int *head;
  comp = 0;

  initialize(g);

  int *stack = new int[g.edges + 2];
  for (int j = 0; j < g.edges + 2; j++) {
    stack[j] = -1;
  }
  head = &stack[g.edges];

  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].number == -1) {
      k = i;
      biconnect(i, 0, -1, comp, head, g);
      g.nlist[k].art--;
    }
  }
  delete[] stack;
  if (comp > 1) {
    u = new graph[comp];
    for (int k = 0; k < comp; k++) {
      int num = 0;
      int *nume = nullptr;
      for (int i = 0; i < g.edges; i++) {
        if (g.elist[i].tree - 1 == k) {
          num++;
        }
      }
      nume = new int[num];
      num = 0;
      for (int i = 0; i < g.edges; i++) {
        if (g.elist[i].tree - 1 == k) {
          nume[num] = i;
          num++;
        }
      }
      splitgraph(num, nume, g, u[k]);
      delete[] nume;
    }
  }
}

int *biconnect(int &i, int v, int u, int &comp, int *head, graph &g) {
  int w;

  if (u >= 0) {
    g.nlist[v].father = &g.nlist[u];
  } else {
    u = v;
  }

  g.nlist[v].number = i++;
  g.nlist[v].lowpt = g.nlist[v].number;

  for (int j = 0; j < g.nlist[v].degree; j++) {
    w = g.elist[g.nlist[v].adj[j]].end1 + g.elist[g.nlist[v].adj[j]].end2 - v;

    if (g.nlist[w].number < 0) {
      if (g.elist[g.nlist[v].adj[j]].st == 0) {
        *head = g.nlist[v].adj[j];
        g.elist[ *head].st = 1;
        head -= 1;
      }
      head = biconnect(i, w, v, comp, head, g);
      g.nlist[v].lowpt = min(g.nlist[v].lowpt, g.nlist[w].lowpt);

      if (g.nlist[w].lowpt >= g.nlist[v].number) {
        g.nlist[v].art++;
        comp++;

        while ( *(head + 1) != -1 &&
          (g.nlist[g.elist[ *(head + 1)].end1].number >= g.nlist[w].number ||
            g.nlist[g.elist[ *(head + 1)].end2].number >= g.nlist[w].number)) {
          g.elist[ *(head + 1)].tree = comp;
          //std::cerr<<g.elist[*(head+1)].index<<" which is ";
          //std::cerr<<g.nlist[g.elist[*(head+1)].end1].index<<" and "<<g.nlist[g.elist[*(head+1)].end2].index;
          //std::cerr<<" are in comp "<<comp<<" \n";

          *(head + 1) = -1;
          head += 1;
        }
      }
    } else if (g.nlist[w].number < g.nlist[v].number &&
      w != g.nlist[v].father - g.nlist) {
      if (g.elist[g.nlist[v].adj[j]].st == 0) {
        *head = g.nlist[v].adj[j];
        g.elist[ *head].st = 1;
        head -= 1;
      }
      g.nlist[v].lowpt = min(g.nlist[v].lowpt, g.nlist[w].number);
    }
  }
  return head;
}

void leightonrao(graph &g) {
  int v;
  int count = 0;
  int sep = 0;
  int e, ee, ww;
  double weight = 0.0, next = 0.0;
  double eps = (double)(g.nodes) / ((double) g.edges *9.0);
  double flux = g.nodes, tempflux;

  for (int i = 0; i < g.edges; i++) {
    g.elist[i].lr = (double) 1 / g.nlist[g.elist[i].end1].degree;
    g.elist[i].lr += (double) 1 / g.nlist[g.elist[i].end2].degree;
    g.elist[i].lr /= 2.0;
    //std::cerr<<g.elist[i].lr<<"\n";
    g.elist[i].tree = 0;
  }

  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].color = 0;
    g.nlist[i].number = 0;
  }

  while (count < (int)(g.nodes / 2) &&sep < (int)(g.nodes / 2)) {
    //std::cerr<<sep<<" sep\n";
    //std::cerr<<(int) (g.nodes-sep)/2<<" nodes-sep\n";
    count = 0;
    weight = 0.0;
    next = 0.0;

    for (int i = 0; i < g.nodes; i++) {
      g.nlist[i].number = 0;
    }
    v = -1;
    for (int i = 0; i < g.nodes; i++) {
      //std::cerr<<g.nlist[i].color<<" color of "<<i<<"\n";
      if ((v < 0 &&g.nlist[i].color == 0) ||
        (g.nlist[i].degree < g.nlist[v].degree &&g.nlist[i].color == 0)) {
        v = i;
      }
    }
    //std::cerr<<v<<" v\n";
    g.nlist[v].color = 1;
    count++;
    flux = (double) g.nlist[v].degree;
    while (weight + next >= (1.0 + flux *eps) *weight) {
      ee = -1;
      weight += next;
      next = 0.0;
      //std::cerr << "new search\n";
      for (int i = 0; i < g.nodes; i++) {
        if (g.nlist[i].color == 1) {
          //std::cerr << i << " node of cut\n";
        }
      }
      for (int i = 0; i < g.edges; i++) {
        int e1 = g.elist[i].end1;
        int e2 = g.elist[i].end2;
        if ((g.nlist[e1].color == 0 &&g.nlist[e2].color == 1) ||
          (g.nlist[e2].color == 0 &&g.nlist[e1].color == 1)) {
          //std::cerr<<i<<" possible edge\n";
          if (ee < 0 || (g.elist[i].lr - g.nlist[e1].number - g.nlist[e1].number) <
            (g.elist[ee].lr - g.nlist[g.elist[ee].end1].color -
              g.nlist[g.elist[ee].end2].number)) {
            ee = i;
          }
        }
      }
      if (ee < 0) {
        //std::cerr << " ERROR ee is neg\n";
        break;
        //exit(-1);
      } else {
        next = g.elist[ee].lr;
        if (g.nlist[g.elist[ee].end1].color == 0) {
          ww = g.elist[ee].end1;
          g.nlist[ww].color = 1;
        } else {
          ww = g.elist[ee].end2;
          g.nlist[ww].color = 1;
        }
        count++;
      }
      int ecut = 0;
      e = 0;
      int ncount = 0;
      for (int i = 0; i < g.edges; i++) {
        int e1 = g.elist[i].end1;
        int e2 = g.elist[i].end2;
        if ((g.nlist[e1].color == 0 &&g.nlist[e2].color == 1) ||
          (g.nlist[e2].color == 0 &&g.nlist[e1].color == 1)) {
          ecut++;
        }
        if (g.nlist[e1].color == 1 &&g.nlist[e2].color == 1) {
          e++;
        }
      }
      for (int i = 0; i < g.nodes; i++) {
        if (g.nlist[i].color == 1) {
          int sum = 0;
          for (int j = 0; j < g.nlist[i].degree; j++) {
            sum = g.nlist[g.elist[g.nlist[i].adj[j]].end1].color;
            sum += g.nlist[g.elist[g.nlist[i].adj[j]].end2].color;
            if (sum == 1) {
              ncount++;
              break;
            }
          }
        }
      }
      //std::cerr << ncount << " middle set cardinality\n";
      tempflux = (double) ncount / min(e, g.edges - e);
      flux = min(flux, tempflux);
      //std::cerr << weight + next << " has to be less than\n";
      //std::cerr << (1.0 + flux *eps) *weight << " this\n";
      //std::cerr << count << " count\n";
      //std::cerr << g.nodes / 2 << " half the nodes\n";
      g.nlist[g.elist[ee].end1].number -= (int) next;
      g.nlist[g.elist[ee].end2].number -= (int) next;

    }
    //std::cerr << g.nodes / 2 << " half the nodes\n";

    //count--;
    //g.nlist[ww].color=0;
    //std::cerr << count << " count\n";
    //std::cerr << sep << " sep\n";
    //std::cerr << g.nodes << " nodes second test\n";
    if (count < (int)((g.nodes) / 2)) {
      sep += count;
      //std::cerr << "look for new region\n";
      for (int i = 0; i < g.nodes; i++) {
        if (g.nlist[i].color == 1) {
          g.nlist[i].color = -2;
          //std::cerr << i << " new attitude\n";
        }
      }
    } else {
      break;
    }
  }
  //std::cerr << sep << " sep and count " << count << "\n";
  int t = 0;
  for (int i = 0; i < g.edges; i++) {
    if (g.nlist[g.elist[i].end1].color < 0 &&g.nlist[g.elist[i].end2].color < 0) {
      //std::cerr << g.elist[i].end1 << " & " << g.elist[i].end2 << " color cut\n";
      g.elist[i].tree = 1;
      t++;
    }
  }
  //std::cerr << t << " t and g.edges" << g.edges << "\n";
  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].color >= 0) {
      for (int j = 0; j < g.nlist[i].degree; j++) {
        if (g.elist[g.nlist[i].adj[j]].tree == 1) {
          // //std::cerr << i << " hello ms\n";
          break;
        }
      }
    }
  }

}

void findcut3(graph &g, int &cuts, int *&cutx, int &es1, int *&side1, int &es2,
  int *&side2) {
  int j, w;
  int cnodes = 0;
  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].x = 0;
    if (g.nlist[i].cut == 1) {
      cnodes++;
    }
  }

  // for(int i=0; i<g.edges; i++){
  //std::cerr<<g.elist[i].end1<<" and "<<g.elist[i].end2<<" edges\n";
  //}
  //graph h;
  //cliqueish(g, h);
  //center(h);
  //std::cerr<<"hello\n";
  //for(int i=0; i<h.nodes; i++){
  //g.nlist[i].x=h.nlist[i].x;
  //}
  //freegraph(h);
  /*if(cnodes==0 &&g.nodes>=100){
    //std::cerr<<cnodes<<" cnodes and nodes "<<g.nodes<<"\n";
    eigengraph(g);
    //std::cerr<<"hello3\n";
  }
  else{*/
  //std::cerr<<"center\n";
  center(g);
  //}

  j = 0;
  for (int i = 0; i < g.edges; i++) {
    if (g.elist[i].wk == 1) {
      //std::cerr<<j<<" j\n";
      j++;
      g.elist[i].wk = 1;
      //std::cerr<<g.nlist[g.elist[i].end1].index<<" % "<<g.nlist[g.elist[i].end2].index<<"\n";
    }
    //std::cerr<<g.nlist[g.elist[i].end1].index<<" the graph "<<g.nlist[g.elist[i].end2].index<<"\n";
  }

  /*for(int i=0; i<g.nodes; i++){
    if(g.nlist[i].x==1){
      g.nlist[i].x=2;
      //std::cerr<<"for potential "<<g.nlist[i].index<<"\n";
      for(int k=0; k<g.nlist[i].degree; k++){
	int e=g.nlist[i].adj[k];
	w=g.elist[e].end1+g.elist[e].end2 -i;
	if(g.elist[e].wk==0){
	  g.nlist[i].x=1;
	  //std::cerr<<g.nlist[i].index<<" cut node\n";
	}	
      }
    }
  }*/
  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].x = 0;
    if (g.nlist[i].degree > 0) {
      int wk = g.elist[g.nlist[i].adj[0]].wk;
      for (int k = 1; k < g.nlist[i].degree; k++) {
        int e = g.nlist[i].adj[k];
        if (g.elist[e].wk != wk) {
          g.nlist[i].x = 1;
          break;
        }
      }
    }
  }

  /*j=0;
    for(int i=0; i<g.edges; i++){
    if(g.nlist[g.elist[i].end1].x>0 &&g.nlist[g.elist[i].end2].x>0){
    j++;
    //std::cerr<<g.nlist[g.elist[i].end1].index<<" % "<<g.nlist[g.elist[i].end2].index<<"\n";
    }
    }
    //std::cerr<<"hello3\n";
    */

  //std::cerr<<j<<" j\n";
  if (j == 0) {
    //std::cerr << j << "\n";
    exit(-1);
  }
  es1 = j;
  es2 = g.edges - es1;
  if (side1) delete[] side1;
  if (side2) delete[] side2;
  side1 = new int[es1];
  //std::cerr<<side1<<" side1 and es2 "<<es2<<"\n";
  side2 = new int[es2];

  //std::cerr<<side1<<" side1\n";
  //std::cerr<<side2<<" side2\n";
  j = 0, w = 0;
  for (int i = 0; i < g.edges; i++) {
    if (g.elist[i].wk == 1) {
      side1[j] = i;
      //std::cerr<<side1[j]<<" side1\n";
      j++;
    } else {
      side2[w] = i;
      //std::cerr<<side2[w]<<" side2\n";
      w++;
    }
  }
  //std::cerr<<" hello again\n";
  j = 0;
  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].x == 1) {
      j++;
    }
  }

  cuts = j;
  //std::cerr<<cuts<<" cuts\n";
  cutx = new int[cuts];
  if (g.width == 0) {
    g.width = cuts;
    //std::cerr<<cuts<<" cuts\n";
  }
  j = 0;
  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].x == 1) {
      cutx[j] = i;
      g.nlist[i].cut = 1;
      j++;
    }
  }
  //std::cerr<<cuts<<" cuts\n";
  //std::cerr<<es1<<" side1 "<<es2<<" side2 "<<cuts<<" cuts\n";
  //showmecut(g, cuts, es1, es2, cutx, side1, side2);
  if (cuts == 0) {
    //std::cerr << cuts << " cuts equal to 0\n";
    //std::cerr << es1 << " side1 and side2 " << es2 << " and edges " << g.edges << "\n";
    for (int i = 0; i < g.nodes; i++) {
      if (g.nlist[i].x != 0) {
        //std::cerr << i << " x is not 0\n";
      }
    }
    for (int i = 0; i < g.edges; i++) {
      //std::cerr<<g.nlist[g.elist[i].end1].index<<" and "<<g.nlist[g.elist[i].end2].index<<" edges\n";
    }
    exit(-1);
  }
}

void dfs(graph &g, int comp, int u) {
  g.nlist[u].number = comp;

  for (int i = 0; i < g.nlist[u].degree; i++) {
    int w = g.elist[g.nlist[u].adj[i]].end1 + g.elist[g.nlist[u].adj[i]].end2 - u;
    if (g.nlist[w].number == 0) {
      dfs(g, comp, w);
    }
  }

}

void center(graph &g) {
  int tcuts, *cutx, *side1, *side2, es1, es2;
  short *p, ** a;
  double factor = 1.0 / 3.0;
  int limit, diam = 0;
  int cnodes = 0, side = 0;
  int cuts = g.nodes, share;
  int work = 0, owork = 0;
  int play = 0, oplay = 0;
  int superv = -1, otop = 1;
  int v;
  int okk, dcount = 0, duck = 0;
  int step = 1;
  graph h;

  h.nodes = 0;

  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].cut == 1) {
      cnodes++;
    }
  }
  if (g.edges >= 250) {
    factor = .1;
  }
  if (g.edges >= 500) {
    step = 2;
  }
  //if(g.nodes >=1100){
  //factor=1.0/5.0;
  //}
  if (g.edges >= 1000) {
    factor = 1.0 / 5.0;
    step = 5;
  }
  //std::cerr<<step<<"\n";
  //std::cerr<<"\n";
  //std::cerr<<cnodes<<" cnodes\n";
  //std::cerr<<g.nodes<<" g's nodes\n";
  //std::cerr<<g.edges<<" g's edges\n";
  //for(int i=0; i<g.edges; i++){
  //std::cerr<<g.elist[i].end1<<" e "<<g.elist[i].end2<<"\n";
  //}
  int ok = 0;
  int last = 0;
  limit = (int)(g.nodes *(g.nodes + 1) / 2);
  p = new short[limit];
  a = new short *[g.nodes];
  for (int i = 0, j = 0; i < g.nodes; i++, j += i) {
    a[i] = &p[j];
    if (j > 0) {
      p[j - 1] = 0;
    }
  }
  for (int i = 0; i < g.nodes - 1; i++) {
    bfs(i, diam, a, g);
  }

  //std::cerr<<diam<<" diameter\n";
  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].number = 0;
    g.nlist[i].token = 0;
    g.nlist[i].color = 0;
  }

  v = -1;
  for (int i = 0; i < g.nodes; i++) {
    for (int j = 0; j < g.nodes; j++) {
      if (i == j) {
        a[i][j] = 0;
      }
      if (a[max(i, j)][min(i, j)] > g.nlist[i].number) {
        g.nlist[i].number = a[max(i, j)][min(i, j)];
        //std::cerr<<i<<"'s number"<<g.nlist[i].number<<"\n";
      }
    }
    //std::cerr<<g.nlist[i].index<<"'s number "<<g.nlist[i].number<<"\n";
    if (g.nlist[i].number == diam || g.nlist[i].cut == 1) {
      //std::cerr<<g.nlist[i].index<<" diam node\n";
      dcount++;
    }
  }
  //std::cerr<<dcount<<" diameter nodes\n";

  for (int i = 0; i < g.nodes; i++) {
    if ((g.nlist[i].number == diam || g.nlist[i].cut == 1) &&g.nlist[i].token == 0) {
      for (int j = 0; j < g.nlist[i].degree; j++) {
        int w = g.elist[g.nlist[i].adj[j]].end1 +
          g.elist[g.nlist[i].adj[j]].end2 - i;
        if ((g.nlist[w].number == diam) &&g.nlist[w].cut != 1 &&
          g.nlist[w].token == 0) {
          g.nlist[w].token = 1;
          //std::cerr<<g.nlist[w].index<<" got changed\n";
          duck++;
        }
      }
    }
  }
  //std::cerr<<duck<<" nodes got changed\n";

  ok = 1;
  while (ok) {
    ok = 1;
    v = -1;
    //if(cnodes > 0){
    for (int i = 0; i < g.nodes; i++) {
      //std::cerr<<i<<" color "<<g.nlist[i].token<<"\n";
      if ((g.nlist[i].number == diam || g.nlist[i].cut == 1) &&
        g.nlist[i].token == 0) {
        //std::cerr<<i<<" color "<<g.nlist[i].token<<"\n";
        v = i;
        break;
      }
    }
    // }
    //else{
    //for(int i=0; i<g.nodes; i++){	
    //std::cerr<<i<<" color "<<g.nlist[i].token<<"\n";
    //if((g.nlist[i].number==diam || g.nlist[i].cut==1)
    //   &&g.nlist[i].token==0){
    //std::cerr<<i<<" color "<<g.nlist[i].token<<"\n";
    //  v=i;
    //  break;
    //}
    //}
    //}
    //std::cerr<<v<<" v\n";
    if (v < 0) {
      ok = 0;
    } else {
      last = v;
      int *weight = new int[g.nodes];
      int *vert = new int[g.nodes];
      int start = roundup((double) g.nodes *factor);
      int end = roundup((double) g.nodes *factor *(1.0 / 2.0));
      //int top=10;
      if (g.nodes <= 6) {
        start = 1;
        end = 1;
      }
      //if(end==1) end++;
      if (cnodes == 0) {
        step = 1;
        if (g.nodes >= 1000) {
          end = start;
        }
      }
      //if( g.nodes >=500){
      //end=start;
      //}
      //step=1;
      int split = 0;
      for (int i = 0; i < g.nodes; i++) {
        weight[i] = a[max(v, i)][min(v, i)];
        //if(i==v) weight[i]=0;
        vert[i] = i;
      }
      if (cnodes > 0) end = 1;
      //if(g.nodes >= 1000){
      //end=roundown((double)g.nodes *factor *(3.0/4.0));
      //}
      //start=1;
      //end=start;
      //std::cerr<<start<<" start and end "<<end<<" for v "<<g.nlist[v].index<<"\n";
      //std::cerr<<v<<" v\n";
      //for(int i=0;i<g.nodes; i++){
      //std::cerr<<vert[i]<<" has "<<weight[i]<<" weight\n";
      //}
      sort1(g.nodes, vert, weight);
      //std::cerr<<"after sort\n";
      //for(int i=0;i<g.nodes; i++){
      //std::cerr<<vert[i]<<" has "<<weight[i]<<" weight\n";
      //}
      //std::cerr<<end<<" end\n";
      for (int top = start; top >= end; top -= step) {
        //std::cerr<<top<<" top\n";
        int count = 0;
        //for(int i=0; i<top; i++){
        //count++;
        //}
        //for(int i=g.nodes-1; i>=g.nodes-top; i--){
        //count++;
        //}
        count = 2 *top;
        int *set = new int[count];
        //std::cerr<<count<<" count\n";
        //std::cerr<<top<<" top\n";
        //std::cerr<<bottom<<" bottom\n";
        count = 0;
        for (int i = 0; i < top; i++) {
          set[count] = vert[i];
          //std::cerr<<g.nlist[vert[i]].index<<" top\n";
          count++;
        }
        split = count;
        for (int i = g.nodes - 1; i >= g.nodes - top; i--) {
          set[count] = vert[i];
          //std::cerr<<g.nlist[vert[i]].index<<" bottom\n";
          count++;
        }
        //delete []vert;
        //delete []weight;

        int source = 0;
        int sink = 0;
        int ncount = 0;
        if (top > 1) {
          flowgraph1(g, count, split, set, source, sink, h);
          okk = cut(h, source, sink, 0, tcuts, cutx, es1, side1, es2, side2);
          int no = 0;
          for (int i = 0; i < split; i++) {
            if (h.nlist[set[i]].x == 1) {
              no++;
            }
          }
          if (top == no) {
            //std::cerr<<tcuts<<" tcuts\n";
            freegraph(h);
            flowgraph(g, count, split, set, source, sink, h);
            okk = cut(h, source, sink, 0, tcuts, cutx, es1, side1, es2, side2);
            //std::cerr<<okk<<" okk\n";
            for (int i = 0; i < g.nodes; i++) {
              g.nlist[i].x = 0;
              if (h.nlist[i].x > 0) {
                g.nlist[i].x = 1;
                ncount++;
              }
            }
            for (int i = 0; i < split; i++) {
              g.nlist[set[i]].x = 1;
              ncount++;
            }
          } else {
            for (int i = 0; i < g.nodes; i++) {
              g.nlist[i].x = 0;
              if (h.nlist[i].x > 0) {
                g.nlist[i].x = 1;
                ncount++;
              }
            }
          }
        } else {
          okk = cut(g, set[0], set[1], 0, tcuts, cutx, es1, side1, es2, side2);
          for (int i = 0; i < g.nodes; i++) {
            if (g.nlist[i].x > 0) {
              ncount++;
            }
          }
        }
        //std::cerr<<okk<<" ok for top "<<top<<"\n";
        if (okk >= 0) {
          int ecount = 0;
          for (int i = 0; i < g.edges; i++) {
            if (g.nlist[g.elist[i].end1].x > 0 &&g.nlist[g.elist[i].end2].x > 0) {
              ecount++;
            }
          }
          delete[] set;
          int e, w;
          for (int i = 0; i < g.nodes; i++) {
            if (g.nlist[i].x == 1) {
              g.nlist[i].x = 2;
              for (int k = 0; k < g.nlist[i].degree; k++) {
                e = g.nlist[i].adj[k];
                w = g.elist[e].end1 + g.elist[e].end2 - i;
                if (g.nlist[w].x == 0) {
                  g.nlist[i].x = 1;
                  /*if(g.nlist[v].index==119){
                    //std::cerr<<g.nlist[i].index<<" possible\n";
                    }*/
                }
              }
            }
          }
          share = 0;
          side = 0;
          for (int i = 0; i < g.nodes; i++) {
            if (g.nlist[i].x == 1 &&g.nlist[i].cut == 1) {
              share++;
              //if(g.nlist[v].index==119){
              //std::cerr<<g.nlist[i].index<<" is shared\n";
              //}
            }
            if (g.nlist[i].x == 2 &&g.nlist[i].cut == 1) {
              side++;
              //if(g.nlist[v].index==119){
              //std::cerr<<g.nlist[i].index<<" is on one side\n";
              //}
            }
            //if(cnodes==0 &&tcuts==5 &&g.nlist[i].x==1){
            //std::cerr<<top<<" top and v "<<g.nlist[v].index<<"\n";
            //std::cerr<<g.nlist[i].index<<" cut node\n";
            //}
          }
          // big=max(ecount, g.edges-ecount);
          work = max(side + tcuts, cnodes - side - share + tcuts);
          play = min(side + tcuts, cnodes - side - share + tcuts);
          //std::cerr<<big<<" big and old big "<<obig<<"\n";
          //std::cerr<<side<<" side and old side "<<oside<<"\n";
          //std::cerr<<tcuts<<" cut num and share "<<share<<"\n";
          //std::cerr<<cuts<<" best cut and share "<<oshare<<"\n";
          //std::cerr<<play<<" play and old play "<<oplay<<"\n";
          //std::cerr<<top<<" top and old top "<<otop<<"\n";
          //std::cerr<<g.nlist[v].index<<" v and superv "<<g.nlist[superv].index<<"\n";
          //std::cerr<<work<<" this";
          //std::cerr<<" should be less than this "<<owork<<" to be the best\n";
          //if(big <=2*mini){
          if (superv < 0 //|| share -tcuts > oshare -cuts){ 
            //|| (share==oshare  &&tcuts < cuts)){
            ||
            (work < owork)
            //|| (work==owork &&tcuts > cuts )
            ||
            (work == owork &&play > oplay)) {
            //|| (work==owork &&play==oplay &&big <=2*mini)){
            //|| (work==owork &&tcuts==cuts &&share > oshare)){
            superv = v;
            cuts = tcuts;
            owork = work;
            oplay = play;
            otop = top;
          }
        } else delete[] set;
        //else{
        //std::cerr<<source<<" source and sink "<<sink<<"\n";
        //for(int i=0;i<h.edges; i++){
        //std::cerr<<h.elist[i].end1<<" h "<<h.elist[i].end2<<"\n";
        //}
        //}
        if (h.nodes) freegraph(h);
        g.nlist[v].token = 1;
        //std::cerr<<v<<" v's color "<<g.nlist[v].token<<"\n";
        for (int i = 0; i < g.nodes; i++) {
          g.nlist[i].x = 0;
        }
      }
      delete[] vert;
      delete[] weight;
    }
    //if(v>=0) std::cerr<<v<<" v's color "<<g.nlist[v].token<<"\n";
  }
  if (superv < 0) {
    superv = last;
    otop = 1;
    //for( int i=0; i<g.edges; i++){
    //std::cerr<<g.elist[i].end1<<" and "<<g.elist[i].end2<<"\n";
    //}
  }
  //std::cerr<<owork<<" optimal work and play "<<oplay<<"\n";
  int *weight = new int[g.nodes];
  int *vert = new int[g.nodes];

  int split = 0;
  for (int i = 0; i < g.nodes; i++) {
    weight[i] = a[max(superv, i)][min(superv, i)];
    vert[i] = i;
  }

  sort1(g.nodes, vert, weight);
  //for(int i=0;i<g.nodes; i++){
  //std::cerr<<weight[vert[i]]<<" weight\n";
  //}

  int count = 0;
  // for(int i=0; i<otop; i++){
  ///std::cerr<<i<<"\n";
  //count++;
  //}
  //for(int i=g.nodes-1; i>=g.nodes-otop; i--){
  //count++;
  //}
  count = 2 *otop;
  int *set = new int[count];
  //std::cerr<<count<<" count\n";
  //std::cerr<<top<<" top\n";
  //std::cerr<<bottom<<" bottom\n";
  count = 0;
  for (int i = 0; i < otop; i++) {
    set[count] = vert[i];
    //std::cerr<<vert[i]<<" top\n";
    count++;
  }
  split = count;
  for (int i = g.nodes - 1; i >= g.nodes - otop; i--) {
    set[count] = vert[i];
    //std::cerr<<vert[i]<<" bottom\n";
    count++;
  }
  delete[] vert;
  delete[] weight;

  int source = 0;
  int sink = 0;
  if (otop > 1) {
    flowgraph1(g, count, split, set, source, sink, h);
    cut(h, source, sink, 0, cuts, cutx, es1, side1, es2, side2);
    //std::cerr<<cuts<<" cuts &superv "<<superv<<"\n";
    int no = 0;
    for (int i = 0; i < split; i++) {
      if (h.nlist[set[i]].x == 1) {
        no++;
      }
    }
    if (no == otop) {
      freegraph(h);
      flowgraph(g, count, split, set, source, sink, h);
      okk = cut(h, source, sink, 0, tcuts, cutx, es1, side1, es2, side2);
      for (int i = 0; i < g.nodes; i++) {
        g.nlist[i].x = 0;
        if (h.nlist[i].x > 0) {
          g.nlist[i].x = 1;
        }
      }
      for (int i = 0; i < split; i++) {
        g.nlist[set[i]].x = 1;
      }
    } else {
      for (int i = 0; i < g.nodes; i++) {
        if (h.nlist[i].x > 0) {
          g.nlist[i].x = 1;
        }
      }
    }
    if (h.nodes) freegraph(h);
    //std::cerr<<owork<<" work and cuts "<<cuts<<"\n";
    //for(int i=0; i<split; i++){
    //g.nlist[set[i]].x=1;
    //std::cerr<<g.nlist[set[i]].index<<" part of top\n";
    //}
  } else {
    cut(g, set[0], set[1], 0, cuts, cutx, es1, side1, es2, side2);
  }
  for (int i = 0; i < g.edges; i++) {
    g.elist[i].wk = 0;
    if (g.nlist[g.elist[i].end1].x > 0 &&g.nlist[g.elist[i].end2].x > 0) {
      g.elist[i].wk = 1;
    }
  }
  delete[] set;
  delete[] p;
  delete[] a;

}

void cliqueish(graph &g, graph &h) {
  int cnodes = 0;
  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].cut == 1) {
      cnodes++;
    }
  }

  int *end1 = new int[g.edges + (int)((cnodes *cnodes - cnodes) / 2)];
  int *end2 = new int[g.edges + (int)((cnodes *cnodes - cnodes) / 2)];

  int count = 0;
  for (int i = 0; i < g.edges; i++) {
    end1[count] = g.elist[i].end1;
    end2[count] = g.elist[i].end2;
    count++;
  }

  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].cut == 1) {
      for (int j = i + 1; j < g.nodes; j++) {
        if (g.nlist[j].cut == 1) {
          end1[count] = i;
          end2[count] = j;
          count++;
        }
      }
    }
  }

  create(g.nodes, count, end1, end2, h);
  for (int i = 0; i < g.nodes; i++) {
    h.nlist[i].cut = g.nlist[i].cut;
  }
}
void flowgraph(graph &g, int num, int split, int *set, int &source, int &sink,
  graph &h) {
  source = g.nodes;
  sink = g.nodes + 1;

  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].color = 0;
  }

  //std::cerr<<split<<" split number\n";
  for (int i = 0; i < num; i++) {
    if (i < split) {
      g.nlist[set[i]].color = 1;
    } else {
      g.nlist[set[i]].color = 2;
      //std::cerr<<set[i]<<" got colored 2\n";

    }
  }

  //std::cerr<<g.edges<<" edges\n";
  int *end1 = new int[g.edges];
  int *end2 = new int[g.edges];
  //std::cerr<<"hello\n";
  int count = 0;
  for (int i = 0; i < g.edges; i++) {
    //std::cerr<<i<<" i\n";
    int u = g.elist[i].end1;
    int v = g.elist[i].end2;
    //std::cerr<<u<<" u and v "<<v<<"\n";
    //if(count==0){
    //std::cerr<<u<<" and "<<v<<" the edge of interest\n";
    //std::cerr<<g.nlist[u].color<<" and "<<g.nlist[v].color<<" their colors\n";
    //}
    if (g.nlist[u].color == 1) {
      end1[count] = source;
    }
    if (g.nlist[u].color == 2) {
      end1[count] = sink;
    }
    if (g.nlist[u].color == 0) {
      end1[count] = u;
    }
    if (g.nlist[v].color == 1) {
      end2[count] = source;
    }
    if (g.nlist[v].color == 2) {
      end2[count] = sink;
    }
    if (g.nlist[v].color == 0) {
      end2[count] = v;
    }
    //if(count==0){
    //std::cerr<<end1[count]<<" also "<<end2[count]<<"\n";
    //}
    count++;
  }

  //std::cerr<<"hello\n";
  create(g.nodes + 2, g.edges, end1, end2, h);
  //for(int i=0 ; i< h.edges; i++){
  //std::cerr<<h.elist[i].end1<<" and "<<h.elist[i].end2<<" h\n";
  //}
  for (int i = 0; i < num; i++) {
    g.nlist[set[i]].color = 0;
  }
  delete[] end1;
  delete[] end2;
}

void flowgraph1(graph &g, int num, int split, int *set, int &source, int &sink,
  graph &h) {

  source = g.nodes;
  sink = g.nodes + 1;

  /*for(int i=0; i<g.nodes; i++){
    g.nlist[i].color=0;
  }

  //std::cerr<<split<<" split number\n";
  for(int i=0; i<num; i++){
    if(i <split){
      g.nlist[set[i]].color=1;
    }
    else{
      g.nlist[set[i]].color=2;
      //std::cerr<<set[i]<<" got colored 2\n";
      
    }
  }*/

  //std::cerr<<g.edges<<" edges\n";
  int *end1 = new int[g.edges + num];
  int *end2 = new int[g.edges + num];
  //std::cerr<<"hello\n";
  int count = 0;
  for (int i = 0; i < g.edges; i++) {
    //std::cerr<<i<<" i\n";
    end1[i] = g.elist[i].end1;
    end2[i] = g.elist[i].end2;
  }
  count = g.edges;
  for (int i = 0; i < num; i++) {
    if (i < split) {
      end1[count] = set[i];
      end2[count] = source;
      count++;
    } else {
      end1[count] = set[i];
      end2[count] = sink;
      count++;
    }
  }
  //std::cerr<<"hello\n";
  create(g.nodes + 2, g.edges + num, end1, end2, h);
  //freegraph(t);
  //for(int i=0 ; i< h.edges; i++){
  //std::cerr<<h.elist[i].end1<<" and "<<h.elist[i].end2<<" h\n";
  //}
  /*for(int i=0; i<num; i++){
    g.nlist[set[i]].color=0;
  }*/
  delete[] end1;
  delete[] end2;
}

int roundup(double d) {

  //std::cerr<<d<<" round\n";
  if ((d - (int) d) > 0) {
    return (int) d + 1;
  } else {
    return (int) d;
  }
}

int roundown(double d) {
  if ((int) d == 0) {
    return 1;
  } else {
    return (int) d;
  }
}

void eigengraph(graph &g) {
  int es1, es2, *cutx;
  int *side1, *side2, cuts;
  double *p, ** a;
  graph h;
  int count = 0;
  double factor = 1.0 / 5.0; //*((double)g.nodes/(double)g.edges);
  //std::cerr<<factor<<" factor\n";
  //std::cerr<<g.edges<<" edges\n";
  a = new double *[g.edges];
  double *y;
  double *x;
  double *z = nullptr;
  double *temp;
  int cnodes = 0;
  int limit = (int)(g.edges *(g.edges + 1) / 2);
  p = new double[limit];

  //if(g.nodes >=2000){
  //factor=1.0/3.0;//*((double)g.nodes/(double)g.edges);
  //}
  //if(g.nodes < 500){
  //factor=1.0/7.5;
  //}
  if (g.nodes > 1000) {
    factor = 1.0 / 3.0;
  }
  for (int i = 0; i < limit; i++) {
    p[i] = 0.0;
  }

  for (int i = 0, j = 0; i < g.edges; i++, j += i) {
    a[i] = &p[j];
  }

  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].cut == 1) {
      g.nlist[i].weight = 1.0 / ((double) g.nlist[i].degree);
      cnodes++;
    } else {
      g.nlist[i].weight = 1.0 / ((double) g.nlist[i].degree - 1.0);
    }
  }
  /*
    for(int i=0; i<g.edges; i++){
    for(int j=i; j<g.edges; j++){
    if(i != j){
    if(g.elist[i].end1== g.elist[j].end1 
    || g.elist[i].end1==g.elist[j].end2){
    a[max(i,j)][min(i,j)]+=
    1.0/((double)g.nlist[g.elist[i].end1].degree -1.0);
    //std::cerr<<(double)g.nlist[g.elist[i].end1].degree -1.0<<" put\n";
    }
    if(g.elist[i].end2== g.elist[j].end1 
    || g.elist[i].end2==g.elist[j].end2){
    a[max(i,j)][min(i,j)]+=
    1.0/((double)g.nlist[g.elist[i].end2].degree -1.0);
    }
    }
    else{
    a[max(i,j)][min(i,j)]=2*.55;
    }
    }
    }
    for(int i=0; i<g.edges; i++){
    for(int j=i; j<g.edges; j++){
    //std::cerr<<"a["<<i<<"]["<<j<<"]= "<<a[max(i,j)][min(i,j)]<<"\n";
    }
    }
    */

  //if(cnodes > 0){
  //count=g.edges+1;
  //factor=1.0/3.0;
  //}
  //else{
  count = g.edges;
  //}
  x = new double[count];
  y = new double[count];

  for (int i = 0; i < count; i++) {
    y[i] = 0.0;
    x[i] = 0.0;
    //g.elist[i].lr=1.0/(sqrt((double)g.nlist[g.elist[i].end1].degree 
    //+ (double)g.nlist[g.elist[i].end2].degree - 2.0));
  }

  int t = count / 2;
  for (int i = 0; i < t; i++) {
    y[2 *i] = 1;
    x[2 *i] = 1;
    y[2 *i + 1] = -1;
    x[2 *i + 1] = -1;
  }

  double diff;
  for (int i = 0; i < count *count; i++) {
    //if(i%count==0){
    //for(int j=0; j<count; j++){
    //std::cerr<<"y["<<j<<"]= "<<y[j]<<"\n";
    //}
    //}
    swap(x, y, temp);
    matmult(g, count, y, x);
    //if(i%10==0){
    roundoff(count, y);
    //roundoff(g.edges, x);
    //normalize(g.edges, y);
    //normalize(g.edges, x);
    //}
    normalize(count, y);
    diff = converge(count, x, y);
    //if(sqrt((diff-odiff)*(diff-odiff)) <= 1.0e-8){
    //std::cerr<<diff<<"\n";
    if (diff <= 1.0e-8) {
      //std::cerr<<i<<" break\n";
      break;
    }
  }

  int *e = new int[g.edges];
  //std::cerr<<e<<" e\n";
  for (int i = 0; i < g.edges; i++) {
    e[i] = i;
    //std::cerr<<y[i]<<" of "<<i<<" "<<g.nlist[g.elist[i].end1].index<<" "<<g.nlist[g.elist[i].end2].index<<"\n";
  }
  //if(count > g.edges)std::cerr<<y[count-1]<<" of "<<g.edges<<"\n";
  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].token = 0;
  }
  /*
  for(int i=0;i<g.edges; i++){
    //std::cerr<<g.nlist[g.elist[e[i]].end1].index<<" & ";
    //std::cerr<<g.nlist[g.elist[e[i]].end2].index<<" have ef = "<<y[i]<<"\n";
  }
  */
  if (count == g.edges) {
    sort2(g.edges, e, y);
  } else {
    z = new double[g.edges];
    for (int i = 0; i < g.edges; i++) {
      z[i] = y[i];
    }
    sort2(g.edges, e, z);
  }
  /*
  //std::cerr<<"\n after sort \n";
  for(int i=0;i<g.edges; i++){
    //std::cerr<<e[i]<<" ";
    //std::cerr<<g.nlist[g.elist[e[i]].end1].index<<" & ";
    //std::cerr<<g.nlist[g.elist[e[i]].end2].index<<" have ef = "<<y[i]<<"\n";
  }
  */
  //exit(-1);

  int dum = roundup(factor *(double) count);
  //if(dum==1) dum++;

  //std::cerr<<dum<<" dum  edges "<<g.edges<<"\n";
  for (int i = 0; i < g.nodes; i++) {
    g.nlist[i].token = 0;
  }
  for (int i = 0; i < dum; i++) {
    ////std::cerr<<e[i]<<" e["<<i<<"]\n";
    if (g.nlist[g.elist[e[i]].end1].token == 0) {
      g.nlist[g.elist[e[i]].end1].token = 1;
      //cn++;
    }
    //if(cn==dum) break;
    if (g.nlist[g.elist[e[i]].end2].token == 0) {
      g.nlist[g.elist[e[i]].end2].token = 1;
      //cn++;
    }
    //if(cn==dum) break;
    //std::cerr<<g.nlist[g.elist[e[i]].end1].index<<" source "<<g.nlist[g.elist[e[i]].end2].index<<"\n";
  }
  for (int i = g.edges - 1; i >= g.edges - dum; i--) {
    if (g.nlist[g.elist[e[i]].end1].token == 0) {
      g.nlist[g.elist[e[i]].end1].token = 2;
      //cn++;
    }
    //if(cn==dum) break;
    if (g.nlist[g.elist[e[i]].end2].token == 0) {
      g.nlist[g.elist[e[i]].end2].token = 2;
      //cn++;
    }
    //if(cn==dum) break;
    //std::cerr<<g.nlist[g.elist[e[i]].end1].index<<" sink "<<g.nlist[g.elist[e[i]].end2].index<<"\n";
  }

  delete[] p;
  delete[] a;
  //delete []y;
  delete[] x;
  //delete []e;

  int cc = 0;
  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].token == 1 || g.nlist[i].token == 2) {
      cc++;
    }
  }
  //std::cerr<<cc<<" cc\n";
  //int flip1=0, flip2=0;
  int *vset = new int[cc];
  //std::cerr<<vset<<" vset\n";
  int c = 0;
  int split = 0;
  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].token == 1) {
      vset[split] = i;
      //std::cerr<<g.nlist[i].index<<" source\n";
      split++;
      c++;
      //if(g.nlist[i].cut==1) flip1=1;
    }
  }

  for (int i = 0; i < g.nodes; i++) {
    if (g.nlist[i].token == 2) {
      vset[c] = i;
      //std::cerr<<g.nlist[i].index<<" sink\n";
      c++;
      //if(g.nlist[i].cut==1) flip2=1;
    }
  }

  int source = 0;
  int sink = 0;
  int ok = 0;
  //std::cerr<<"flow\n";
  flowgraph1(g, cc, split, vset, source, sink, h);
  /*if(flip2==1 &&flip1==0){
    swap(source, sink, flip1);
    //std::cerr<<source<<" source and g.nodes "<<g.nodes<<"\n";
  }*/
  //std::cerr<<" another flow\n";
  ok = cut(h, source, sink, 0, cuts, cutx, es1, side1, es2, side2);
  //std::cerr<<ok<<" ok\n";
  //std::cerr<<cuts<<" cuts\n";

  if (ok < 0) {
    //std::cerr << ok << " nodes to close\n";
    delete[] vset;
    freegraph(h);
    for (int i = 0; i < g.edges; i++) {
      g.elist[e[i]].wk = 0;
      //std::cerr<<y[i]<<" of "<<e[i]<<"\n";
      //std::cerr<<g.nlist[g.elist[e[i]].end1].index<<" "<<g.nlist[g.elist[e[i]].end2].index<<"\n";
      if (y[i] <= 1.0e-8) {
        //std::cerr<<y[i]<<" of "<<e[i]<<" winner\n";
        //std::cerr<<g.nlist[g.elist[e[i]].end1].index<<" "<<g.nlist[g.elist[e[i]].end2].index<<"\n";
        g.nlist[g.elist[e[i]].end1].x = 1;
        g.nlist[g.elist[e[i]].end2].x = 1;
        g.elist[e[i]].wk = 1;
      }
    }
    /*for(int i=0; i<g.nodes; i++){
      if(g.nlist[i].x==1){
      g.nlist[i].x=2;
      for(int j=0; j<g.nlist[i].degree; j++){
      if(g.elist[g.nlist[i].adj[j]].wk==0){
      g.nlist[i].x=1;
      break;
      }
      }
      }
      }
      for(int i=0; i<g.nodes; i++){
      if(g.nlist[i].x==2){
      g.nlist[i].x=0;
      }
      }
      */
    delete[] y;
    delete[] e;
  } else {
    delete[] e;
    delete[] y;
    for (int i = 0; i < g.nodes; i++) {
      if (h.nlist[i].x > 0) {
        g.nlist[i].x = 1;
        //std::cerr<<g.nlist[i].index<<" same side\n";
      }
    }
    freegraph(h);
    /*for(int i=0; i<split; i++){
      g.nlist[vset[i]].x=1;
    }*/
    for (int i = 0; i < g.edges; i++) {
      g.elist[i].wk = 0;
      if (g.nlist[g.elist[i].end1].token != 2 ||
        g.nlist[g.elist[i].end2].token != 2) {
        if (g.nlist[g.elist[i].end1].x > 0 &&g.nlist[g.elist[i].end2].x > 0) {
          g.elist[i].wk = 1;
        }
      }
    }
    delete[] vset;
  }
  if (z) delete[] z;
  /*
    for(int i=0; i<dum; i++){
    //std::cerr<<"y["<<i<<"] = "<<y[i]<<"\n";
    //std::cerr<<g.nlist[g.elist[i].end1].index<<" real edge ";
    // //std::cerr<<g.nlist[g.elist[i].end2].index<<" and e="<<i<<"\n";
    g.nlist[g.elist[e[i]].end1].x=1;
    g.nlist[g.elist[e[i]].end2].x=1;
    //std::cerr<<g.nlist[g.elist[i].end1].index<<" gets marked ";
    //std::cerr<<g.nlist[g.elist[i].end2].index<<" and e="<<i<<"\n";
    }
    //std::cerr<<"hello\n";
    delete []y;
    //std::cerr<<p<<" p\n";
    delete []p;
    //std::cerr<<a<<" a\n";
    delete []a;
    delete []x;
    delete []e;
    if(z) delete []z;
  */

}
double converge(int limit, double *x, double *y) {

  double sum = 0.0;
  for (int i = 0; i < limit; i++) {
    //std::cerr<<"x["<<i<<"]="<<x[i]<<" y["<<i<<"]="<<y[i]<<"\n";
    //std::cerr<<x[i]-y[i]<<" xi-yi\n";
    sum += (x[i] - y[i]) *(x[i] - y[i]);
  }

  //std::cerr<<sum<<" sum and sqrt(sum)="<<sqrt(sum)<<"\n";
  return sqrt(sum);
}

void matmult(graph &g, int count, double *y, double *x) {

  //for(int i=0; i<g.edges; i++){
  //std::cerr<<"x["<<i<<"] = "<<x[i]<<"\n";
  //std::cerr<<"y["<<i<<"] = "<<y[i]<<"\n";

  //}
  //std::cerr<<x<<" x and y "<<y<<"\n";
  //for(int i=0; i<g.edges; i++){
  //x[i]=y[i];
  //}

  int cnodes = 0;
  double c = 0;
  if (count > g.edges) {
    for (int i = 0; i < g.nodes; i++) {
      if (g.nlist[i].cut == 1) {
        cnodes++;
      }
    }
    c = 1.55 *cnodes;
  } else {
    c = 1.55 *2;
  }

  for (int i = 0; i < g.edges; i++) {
    y[i] = 0.0;
    int u = g.elist[i].end1;
    int v = g.elist[i].end2;
    for (int j = 0; j < g.nlist[u].degree; j++) {
      if (g.nlist[u].adj[j] != i) {
        //double z=g.elist[i].lr*g.elist[g.nlist[u].adj[j]].lr;
        //y[i]+=z*x[g.nlist[u].adj[j]];
        y[i] += g.nlist[u].weight *x[g.nlist[u].adj[j]];
      }
    }
    for (int j = 0; j < g.nlist[v].degree; j++) {
      if (g.nlist[v].adj[j] != i) {
        //double z=g.elist[i].lr*g.elist[g.nlist[v].adj[j]].lr;
        //y[i]+=z*x[g.nlist[v].adj[j]];
        y[i] += g.nlist[v].weight *x[g.nlist[v].adj[j]];
      }
    }
    if (count > g.edges) {
      if (g.nlist[u].cut == 1) {
        y[i] += g.nlist[u].weight *x[count - 1];
      }
      if (g.nlist[v].cut == 1) {
        y[i] += g.nlist[v].weight *x[count - 1];
      }
    }
    y[i] += (c - 2) *x[i];
    //y[i]+=2*x[i];
  }

  if (count > g.edges) {
    int k = count - 1;
    y[k] = 0.0;
    for (int i = 0; i < g.nodes; i++) {
      if (g.nlist[i].cut == 1) {
        for (int j = 0; j < g.nlist[i].degree; j++) {
          y[k] += g.nlist[i].weight *x[g.nlist[i].adj[j]];
        }
      }
    }
    y[k] += (c - cnodes) *x[k];
  }
}

void eigengraph1(graph &g) {
  int es1, es2, *cutx;
  int *side1, *side2, cuts;
  double *p, ** a;
  graph h;
  double factor = 1.0 / 5.0;
  a = new double *[g.nodes];
  double *y = new double[g.nodes];
  double *x = new double[g.nodes];
  double *temp;
  int limit = (int)(g.nodes *(g.nodes + 1) / 2);
  p = new double[limit];

  if (g.edges >= 1000) {
    factor = .01;
  }
  for (int i = 0; i < limit; i++) {
    p[i] = 0.0;
  }

  for (int i = 0, j = 0; i < g.nodes; i++, j += i) {
    a[i] = &p[j];
    //if(j>0){
    //p[j-1]=0.0;
    //}
  }

  for (int i = 0; i < g.nodes; i++) {
    y[i] = 0.0;
  }

  int t = g.nodes / 2;
  for (int i = 0; i < t; i++) {
    y[2 *i] = 1;
    x[2 *i] = 1;
    y[2 *i + 1] = -1;
    x[2 *i + 1] = -1;
  }

  double diff;
  for (int i = 0; i < 20 *g.nodes; i++) {
    //for(int j=0; j<g.nodes; j++){
    //x[j]=y[j];
    //}
    swap(x, y, temp);
    matmult1(g, y, x);
    //if(i%10==0){
    roundoff(g.nodes, y);
    //}
    normalize(g.nodes, y);
    diff = converge(g.nodes, x, y);
    if (diff <= 1.0e-8) {
      //std::cerr<<i<<" break\n";
      break;
    }
  }

  int *e = new int[g.nodes];
  //std::cerr<<e<<" e\n";
  for (int i = 0; i < g.nodes; i++) {
    e[i] = i;
  }

  sort2(g.nodes, e, y);

  int dum = roundup(factor *(double) g.nodes);

  //std::cerr<<dum<<" dum\n";

  delete[] p;
  delete[] a;
  //delete []y;
  delete[] x;
  //delete []e;

  int count = 2 *dum;

  //std::cerr<<count<<" count\n";
  int *vset = new int[count];
  //std::cerr<<vset<<" vset\n";
  int c = 0;
  int split = 0;
  for (int i = 0; i < dum; i++) {
    vset[split] = e[i];
    //std::cerr<<i<<" source\n";
    split++;
    c++;
  }

  for (int i = g.nodes - 1; i >= g.nodes - dum; i--) {
    vset[c] = e[i];
    //std::cerr<<i<<" sink\n";
    c++;
  }

  //delete []e;
  int source = 0;
  int sink = 0;
  int ok = 0;
  //std::cerr<<"flow\n";
  flowgraph(g, count, split, vset, source, sink, h);
  //std::cerr<<" another flow\n";
  ok = cut(h, source, sink, 0, cuts, cutx, es1, side1, es2, side2);
  //std::cerr<<ok<<" ok\n";
  //std::cerr << cuts << " cuts\n";
  if (ok < 0) {
    freegraph(h);
    delete[] vset;
    //std::cerr << ok << " nodes to close\n";
    for (int i = 0; i < g.nodes; i++) {
      //std::cerr<<g.nlist[e[i]].index<<" has "<<y[i]<<"\n";
      if (y[i] <= 0.0) {
        g.nlist[e[i]].x = 1;
      }
    }
    delete[] e;
    delete[] y;
  } else {
    delete[] e;
    delete[] y;
    for (int i = 0; i < g.nodes; i++) {
      if (h.nlist[i].x > 0) {
        g.nlist[i].x = 1;
      }
    }
    freegraph(h);
    for (int i = 0; i < split; i++) {
      g.nlist[vset[i]].x = 1;
    }
    delete[] vset;
  }
  /*
  for(int i=0; i<dum; i++){
  //std::cerr<<"y["<<i<<"] = "<<y[i]<<"\n";
  //std::cerr<<g.nlist[g.elist[i].end1].index<<" real edge ";
  // //std::cerr<<g.nlist[g.elist[i].end2].index<<" and e="<<i<<"\n";
  g.nlist[g.elist[e[i]].end1].x=1;
  g.nlist[g.elist[e[i]].end2].x=1;
  //std::cerr<<g.nlist[g.elist[i].end1].index<<" gets marked ";
  //std::cerr<<g.nlist[g.elist[i].end2].index<<" and e="<<i<<"\n";
  }
  //std::cerr<<"hello\n";
  delete []y;
  //std::cerr<<p<<" p\n";
  delete []p;
  //std::cerr<<a<<" a\n";
  delete []a;
  delete []x;
  delete []e;
  */

}

void matmult1(graph &g, double *y, double *x) {

  //std::cerr<<x[0]<<" x[0]\n";
  for (int i = 0; i < g.nodes; i++) {
    y[i] = 0.0;
    for (int j = 0; j < g.nlist[i].degree; j++) {
      int u = g.elist[g.nlist[i].adj[j]].end1 +
        g.elist[g.nlist[i].adj[j]].end2 - i;
      double z = (double)(g.nlist[u].degree *g.nlist[i].degree);
      y[i] += (1.0 / sqrt(z)) *x[u];
    }
    y[i] += 1.1 *x[i];
  }
}

void normalize(int limit, double *y) {
  double sum = 0.0;

  for (int i = 0; i < limit; i++) {
    sum += y[i] *y[i];
  }

  sum = sqrt(sum);

  if (sum != 0.0) {
    for (int i = 0; i < limit; i++) {
      y[i] /= sum;
    }
  }
}

void roundoff(int limit, double *y) {
  double sum = 0.0;
  for (int i = 0; i < limit; i++) {
    sum += y[i];
  }

  if (sum != 0.0) {
    for (int i = 0; i < limit; i++) {
      y[i] -= (sum / ((double) limit));
    }
  }

}

void eunionn(int end1, int end2, edge *elist) {
  elink(efind(end1, elist), efind(end2, elist), elist);
}

void elink(int end1, int end2, edge *elist) {
  //std::cout<<"hi\n";
  if (elist[end1].mark > elist[end2].mark) {
    elist[end2].parent = end1;
  } else {
    elist[end1].parent = end2;
    if (elist[end1].mark == elist[end2].mark) {
      elist[end2].mark++;
    }
  }
  //std::cout<<" end link\n";
}


int efind(int n, edge *elist) {
  int temp;
  //std::cout<<"find\n";
  //std::cout<<elist[n].parent<<" parent\n";
  //std::cout<<n<<" n\n";
  if (elist[n].parent != n) {
    temp = elist[n].parent;
    elist[n].parent = efind(temp, elist);
  }
  return elist[n].parent;
}
