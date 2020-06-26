#include <stdlib.h>
#include <stdlib.h> //for Rice
#include<iostream> //for Rice
#include<fstream>
#include<iostream>
#include<math.h>

#define min(i, j)(i <= j) ? i : j
#define max(i, j)(i <= j) ? j : i
#define swap(a, b, t)(((t) = (a)), ((a) = (b)), ((b) = (t)))

struct node {
  int *adj,
    degree,
    x,
    cut,
    tree,
    index,
    number,
    lowpt,
    art,
    color,
    token;
  double weight;
  struct node *father;
  struct edge *forward,
    *back;
};

struct edge {
  int tree,
  end1,
  end2,
  index,
  path,
  wk, parent, mark,
  st;
  double lr;
  struct edge *father;
  struct node *tail;
  struct bnode *holder;
};

struct graph {
  int nodes, edges;
  int width;
  struct node *nlist;
  struct edge *elist;
  struct bnode *bn;
};

/*structures for bgraph*/
typedef struct list {
  int index;
  struct list *next;
}
list;

typedef struct alist {
  struct bedge *be;
  struct alist *next;
}
alist;

typedef struct bnode {
  int index, degree, enodes;
  int mark, head;
  struct list *arcs;
  struct alist *adj;
  struct bnode *next, *parent;
}
bnode;

typedef struct bedge {
  int index, order, color,
  end1,
  end2;
  int *ms, *msdeg;
  struct bedge *next;
}
bedge;

typedef struct bgraph {
  int nodes, edges, width;
  struct bnode *nlist;
  struct bedge *elist;
  struct bqueue *head, *tail;
}
bgraph;

typedef struct queue {
  int elem;
  struct queue *next;
}
queue;

typedef struct bqueue {
  bnode *bv;
  struct bqueue *next;
}
bqueue;

void components(graph &g, int &comp, graph *&u);
void bwcomps(graph &bigg, graph &g, bgraph &b);
void bdecomp(graph &bigg, graph &g, bgraph &b);
void augment(node *v, edge *e, node *source, node *nlist);
int push(int v, int u, int e, int source, int sink, int cut,
  node *nlist, edge *elist);
void cleartree(int nodes, int nedges, node *nlist, edge *elist);
int cut(graph &g, int source, int sink, int opt, int &cut, int *&X, int &es1,
  int *&side1, int &es2, int *&side2);
void create(int nodes, int edges, int *end1, int *end2, graph &g);
void initialize(graph &g);
void bfs(int pp, int &bpath, short ** a, graph &d);
void freegraph(graph &g);
void enqueue(int w, queue *&tail);
void bcreate(bgraph &b);
void badde(bgraph &b, bedge &e);
void baddn(bgraph &b, bnode &n);
void swapedges(int e, bnode *n1, bnode *n2, graph &bigg);
void freebgraph(bgraph &b);
void split(graph &bigg, graph &g, int &cuts, int *&cut, int &ecuts, int *&ecut,
  int &ecuts1, int *&ecut1, bnode *bn, bgraph &b);
void onesplit(graph &g, int &cuts, int *&cut, int &ecuts,
  int *&ecut, int &ecuts1, int *&ecut1);
void splitgraph(int ecuts, int *ecut, graph &g, graph &g0);
void sort(int num, int *sorte);
void findcut1(graph &g, int &cuts, int *&cutx, int &es1, int *&side1, int &es2,
  int *&side2);
void findcut2(graph &g, int &cuts, int *&cutx, int &es1, int *&side1, int &es2,
  int *&side2);
void findcut3(graph &g, int &cuts, int *&cutx, int &es1, int *&side1, int &es2,
  int *&side2);
void onecut(graph &g, int &cuts, int *&cutx, int &es1, int *&side1, int &es2,
  int *&side2);
void unionn(int end1, int end2, bnode *bnlist);
void link(bnode *n1, bnode *n2);
bnode *find(bnode *n);
void eunionn(int end1, int end2, edge *bnlist);
void elink(int n1, int n2, edge *e);
int efind(int i, edge *e);

bnode *midcliquefinder(int &ecuts, int *&ecut, bnode *bn, bgraph &b, graph &g,
  graph &bigg);
bnode *cliquefinder(int &ecuts, int *&ecut, bnode *bn, bgraph &b, graph &g,
  graph &bigg);
void postdfs(bnode *v, bgraph &b);
void bwidth(bnode *bn, bgraph &b, graph &g);
void fillin(bnode *bn, bgraph &b, graph &g, int &count, int *v);
void bconnect(graph &g, bgraph &b, graph &bigg);
void showmecut(graph &g, int cuts, int es1, int es2, int *cutx, int *side1,
  int *side2);
int *biconnect(int &i, int v, int u, int &comp, int *head, graph &g);
void bicomps(graph &g, int &comp, graph *&u);
void blink(int e, int ee, graph &g, bgraph &b);
void bigcliquefinder(int &ecuts, int *&ecut, int &ecuts1, int *&ecut1,
  bnode *bn, bgraph &b, graph &g, graph &bigg);
void leightonrao(graph &g);
void dfs(graph &g, int comp, int u);
void flowgraph(graph &g, int num, int split, int *set, int &source, int &sink,
  graph &h);
void flowgraph1(graph &g, int num, int split, int *set, int &source, int &sink,
  graph &h);
void center(graph &g);
void sort1(int num, int *sorte, int *weight);
int roundup(double d);
int roundown(double d);
void cliqueish(graph &g, graph &h);
void eigengraph(graph &g);
void matmult(graph &g, int count, double *y, double *x);
void eigengraph1(graph &g);
void matmult1(graph &g, double *y, double *x);
void normalize(int limit, double *y);
void roundoff(int limit, double *y);
double converge(int limit, double *x, double *y);
void sort2(int num, int *sorte, double *weight);