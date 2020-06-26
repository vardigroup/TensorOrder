#include <iostream.h>
#include <fstream.h>
#include <math.h>
#include "cut.h"
#define min(i,j)(i<=j)?i:j
#define max(i,j)(i<=j)?j:i      
#define swap(a,b,t) (((t)=(a)),((a)=(b)),((b)=(t)))

void bcreate(bgraph &b)
{
  b.width=0;
  b.nodes=0;
  b.edges=0;
  b.head=NULL;
  b.tail=NULL;
  b.elist=NULL;
  b.nlist=NULL;
}

void bconnect(graph &g, bgraph &b, graph &bigg)
{
  bnode *n=NULL;
  list *l;
  n=new bnode[1];
  g.bn=n;
  n->degree=0;
  n->enodes=g.edges;
  n->next=NULL;
  n->head=0;
  n->arcs=NULL;
  baddn(b, n[0]);

  n->enodes=g.edges;

  for(int i=0; i<g.edges; i++){
    l=new list[1];
    l->index=g.elist[i].index;
    bigg.elist[g.elist[i].index].holder=n;
    l->next=n->arcs;
    n->arcs=l;
    l=NULL;
  }
  
  
 
}

void badde(bgraph &b, bedge &e)
{
  alist *a, *aa;
  bedge *prev=b.elist;
  e.next=NULL;
  e.index=b.edges;
  b.edges++;

  e.order=0;
  e.color=0;
  e.ms=NULL;
  e.msdeg=NULL;
  /*if(b.elist){
    
    for(bedge *i=b.elist->next; i; i=i->next){
      prev=i;
    }
    prev->next=&e;
  }
  else{
    b.elist=&e;
  }*/
  e.next=b.elist;
  b.elist=&e;
  for(bnode *i=b.nlist; i; i=i->next){
    if(i->index==e.end1){
      a=new alist[1];
      a->be=&e;
      a->next=i->adj;
      i->adj=a;
      i->degree++;
    }
    if(i->index==e.end2){
      aa=new alist[1];
      aa->be=&e;
      aa->next=i->adj;
      i->adj=aa;
      i->degree++;
    }
  }

 
}

void baddn(bgraph &b, bnode &n)
{
  n.adj=NULL;
  n.mark=0;
  n.parent=NULL;
  n.head=0;
  n.arcs=NULL;
  n.degree=0;
  n.enodes=0;
  n.index=b.nodes++;
  n.next=b.nlist;
  b.nlist=&n;
  
}

void swapedges(int e, bnode *n1, bnode *n2, graph &bigg)//from n1 to n2
{

  /*list *want=NULL, *prev=NULL;
  if(n1->index==0){
	  cerr<<n1->index<<" n1 and n2 "<<n2->index<<"\n";
  	cerr<<n1->arcs<<" n1->arcs\n";
  	cerr<<n1->arcs->index<<" n1->arcs_>index\n";
  }
  for(list *l=n1->arcs; l!=NULL; l=l->next){
    //cerr<<l->index<<" l\n";
    if(l->index==e){
      //cerr<<l->index<<" found you\n";
      want=l;
      break;
    }
    prev=l;
  }
  if(prev){
    prev->next=want->next;
  }
  else{
    n1->arcs=want->next;
  }
  //cerr<<want<<" want\n";
  //cerr<<want->index<<" want's index\n";
  want->next=n2->arcs;
  bigg.elist[e].holder=n2;
  n2->arcs=want;
  n1->enodes--;
  n2->enodes++;
  //cerr<<"hello\n";
  */

  list *want;
  int *ei=new int[n1->enodes-1];

   int count=0;
   //cerr<<n1->arcs<<" n1->arcs\n";
   for(list *l=n1->arcs, *lnext; l; l=lnext){
       lnext=l->next;
       if(l->index==e){
	  want=l;
       }
       else{
          ei[count]=l->index;
          count++;
          delete []l;
       }
   }
   n1->arcs=NULL;
    want->next=n2->arcs;
    bigg.elist[e].holder=n2;
    n2->arcs=want;
    n1->enodes--; 
    n2->enodes++; 
 
    for(int i=0; i<n1->enodes; i++){
       list *l=new list[1];
       l->index=ei[i];
       l->next=n1->arcs;
       n1->arcs=l;
    }
    delete []ei;
    ei=NULL;



}

void freebgraph(bgraph &b)
{
  bedge *enext;
  bnode *nnext=NULL, *start=NULL;
  list  *anext;
  bqueue *qnext;
  alist *adjnext;

  for(bedge *i=b.elist; i; i=enext){
    enext=i->next;
    if(i->order >0) delete []i->ms;
    if(i->order >0) delete []i->msdeg;
    if(i) delete []i;
  }
  //cerr<<"hello\n";
  for(bnode *i=b.nlist; i; i=nnext){
    nnext=i->next;
    //cerr<<i<<" i && i's arcs "<<i->arcs<<" \n";
    if(i->arcs != NULL){
      for(list *j=i->arcs; j; j=anext){
	anext=j->next;
	//cerr<<j<<" j\n";
	if(j) delete []j;
      }
    }
    if(i->degree >0){
      for(alist *a=i->adj; a; a=adjnext){
	adjnext=a->next;
	delete []a;
      }
    }
    //cerr<<i<<" hello\n";
    if(i) delete []i;
  }
  for(bqueue *q=b.head; q; q=qnext){
    qnext=q->next;
    delete []q;
  }
  
  //delete &b;
  //cerr<<"freebgraph\n";
}

void cutdfs(bnode *v, bnode *superv, int &outnum, bool *cutout, bgraph &b)
{
  int want;
  bnode *w;
  for(alist *e=v->adj; e; e=e->next){
    want=e->be->end1 + e->be->end2 - v->index;
    if(cutout[want]==false){
      for(bnode *n=b.nlist; n; n=n->next){
	if(n->index==want){
	  w=n;
	  break;
	}
      }
      if(w != superv){
	cutout[want]=true;
	outnum++;
	cutdfs(w, superv, outnum, cutout, b);
      }
    }
  }
}

void freesubbgraph(bnode *bn, bgraph &b, graph &bigg)
{
  bool *cutout=new bool[b.nodes];
  int oldbnodes=b.nodes;
  int outnum=0;

  for(int i=0; i<b.nodes; i++){
    cutout[i]=false;
  }

  cutdfs(bn, bn, outnum, cutout, b);

  int outenum=0;
  bedge *enext, *eprev=NULL;
  bnode *nnext=NULL, *start=NULL;
  list  *anext;
  bqueue *qnext;
  alist *adjnext;

 
  for(bedge *i=b.elist; i; i=enext){
    enext=i->next;
    if(cutout[i->end1]==true || cutout[i->end2]==true){
      if(eprev==NULL){
	b.elist=enext;
      }
      else{
	eprev->next=enext;
      }
      outenum++;
      if(i->order >0) delete []i->ms;
      if(i->order >0) delete []i->msdeg;
      if(i) delete []i;
    }
    else{
      eprev=i;
    }
  }

  for(bnode *i=b.nlist; i; i=nnext){
    nnext=i->next;
    if(cutout[i->index]==true || i==bn){
      //cerr<<i<<" i && i's arcs "<<i->arcs<<" \n";
      if(i->degree >0){
	for(alist *a=i->adj; a; a=adjnext){
	  adjnext=a->next;
	  delete []a;
	}
	i->degree=0;
	i->adj=NULL;
      }
    }
    //cerr<<i<<" hello\n";
    if(cutout[i->index]==true){
      if(start==NULL){
	b.nlist=nnext;
      }
      else{
	start->next=nnext;
      }
      if(i->arcs != NULL){
	for(list *j=i->arcs; j; j=anext){
	  anext=j->next;
          if(i->index==0) cerr<<" here in freesubbgraph\n";
	  swapedges(j->index, i, bn, bigg);
	  //cerr<<j<<" j\n";
	}
	i->arcs=NULL;
	i->enodes=0;
      }
      if(i) delete []i;
    }
    else{
      start=i;
    }
  }
  b.nodes-=outnum;
  b.edges-=outenum;

  bn->index=b.nodes-1;
  delete []cutout;
}
  
void split(graph &bigg, graph &g, int &cuts, int* &cut, int &ecuts, int* &ecut,
 	   int &ecuts1, int* &ecut1, bnode *bn, bgraph &b)
{
  int temp, w=cuts;
  bnode *n, *nn; 
  cerr<<g.edges<<" g's edges\n";
  cerr<<ecuts<<" ecuts "<<ecuts1<<" ecuts1\n";
  int cn=(int)(2*g.nodes/3);
  cerr<<bn->index<<" bn and bn->degree "<<bn->degree<<"\n";
  cerr<<cuts<<" cuts and cn "<<cn<<"\n";

  /*if(bn->degree >0 && cuts > cn){
    freesubbgraph(bn, b, bigg);
    int *acut=new int[bn->enodes];
    int ac=0;
    for(list *l=bn->arcs; l; l=l->next){
      acut[ac]=l->index;
      ac++;
    }
    graph g0;
    g0.nodes=0;
    g0.nlist=NULL;
    g0.elist=NULL;

    splitgraph(bn->enodes, acut, bigg, g0);

    bigcliquefinder(ecuts, ecut, ecuts1, ecut1, bn, b, g, bigg);
    
    if(cut) delete []cut;
    if(ecut) delete []ecut;
    if(ecut1) delete []ecut1;
    if(acut) delete []acut;
    cut=NULL, ecut=NULL, ecut1=NULL;
    acut=NULL;
    freegraph(g0);
    return;
       
  }*/
 
  bigg.width=max(bigg.width, cuts);
  

  if(bn->degree==0){
    cerr<<"condition 0\n";
    int ce=(int)(g.nodes*(g.nodes-1)/2);
    if(g.edges==ce || cuts > cn){
      
      bigcliquefinder(ecuts, ecut, ecuts1, ecut1, bn, b, g, bigg);
      
      if(cut) delete []cut;
      if(ecut) delete []ecut;
      if(ecut1) delete []ecut1;
      cut=NULL, ecut=NULL, ecut1=NULL;
      
    }
    else{
      graph g1, g0;
      g0.nodes=0, g1.nodes=0;
      g0.nlist=NULL;
      g0.elist=NULL;
      g1.nlist=NULL;
      g1.elist=NULL;
      
      n=new bnode[1];
      
      n->degree=0;
      n->enodes=0;
      n->arcs=NULL;
      n->next=NULL;
      n->head=1;
      baddn(b, n[0]);
      bedge *e=new bedge[1];
      e->end1=bn->index;
      e->end2=n->index;
      badde(b, e[0]);
      bnode *obn=bn;
      //cerr<<obn<<" before cliquefinder\n";
      //cerr<<ecut1<<" ecut1\n";
      //bn=midcliquefinder(ecuts, ecut, ecuts1, ecut1,bn, b, g, bigg);
      //cerr<<ecut1<<" ecut1\n";
      if(bn->index==0) cerr<<" here in bn->degree==0\n";
      for(int i=0; i<ecuts1; i++){
	swapedges(g.elist[ecut1[i]].index, bn, n, bigg);
      }
      cerr<<ecuts<<" ecuts and ecuts1 "<<ecuts1<<"\n";
      bn=midcliquefinder(ecuts, ecut, bn, b, g, bigg);
      n=midcliquefinder(ecuts1, ecut1, n, b, g, bigg);
      cerr<<ecuts<<" ecuts and ecuts1 "<<ecuts1<<"\n";
      cerr<<bn<<" after cliquefinder\n";
      cerr<<bn->arcs<<" arcs pointer\n";
      if(ecuts > 0){
	splitgraph(ecuts, ecut, g, g0);
      }
      //splitgraph(ecuts1, ecut1, g, g1);
      //freegraph(g);
      delete []ecut;
      ecut=NULL;
      int *ncut=NULL, *necut=NULL;
      int ncuts, necuts;
      cerr<<g0.edges<<" g0's edges\n";
      if(ecuts >1){
	g0.width=bigg.width;
	onecut(g0, ncuts, ncut, ecuts, ecut, necuts, necut);
	
	//cerr<<ecuts<<" ecuts &  ecuts1 "<<necuts<<"\n";
	split(bigg, g0, ncuts, ncut, ecuts, ecut, necuts, necut, bn, b);
      }
      //cerr<<"hello\n";
      freegraph(g0);
      if(ncut) delete []ncut;
      if(ecut) delete []ecut;
      if(necut) delete []necut;
      ncut=NULL, ecut=NULL, necut=NULL;
      
      cerr<<"next big graph\n";
      if(ecuts1 >0){
	splitgraph(ecuts1, ecut1, g, g1);
      }
      if(cut) delete []cut;
      if(ecut) delete []ecut;
      if(ecut1) delete []ecut1;
      cut=NULL, ecut=NULL, ecut1=NULL;
      if(ecuts1 >1 ){
	g1.width=bigg.width;
	onecut(g1, cuts, cut, ecuts, ecut, ecuts1, ecut1);
	
	cerr<<ecuts<<" ecuts &  ecuts1 "<<ecuts1<<"\n";
	split(bigg, g1, cuts, cut, ecuts, ecut, ecuts1, ecut1, n, b);
      }
      freegraph(g1);
      if(cut) delete []cut;
      if(ecut) delete []ecut;
      if(ecut1) delete []ecut1;
      cut=NULL, ecut=NULL, ecut1=NULL;
    }
  }
  else{
    //if(ecuts >1){
    cerr<<bn->index<<"cf1\n";
    n=cliquefinder(ecuts, ecut, bn, b, g, bigg);
    cerr<<n<<" n next cf\n";
    nn=cliquefinder(ecuts1, ecut1, bn, b, g, bigg);
    cerr<<nn<<" nn end of cf2\n";
    cerr<<nn->arcs<<" arcs \n";
    //}
    //cerr<<ecuts<<" ecuts and ecuts1 "<<ecuts1<<"\n";
    if(ecuts==0){
    }
    if(ecuts1==0){
    }
    if(ecuts==1){
      cerr<<"cond 11\n";
      bnode *nv=new bnode[1];
      nv->degree=0;
      nv->enodes=0;
      nv->arcs=NULL;
      nv->next=NULL;
      nv->head=1;
      baddn(b, nv[0]);
      bedge *e=new bedge[1];
      e->end1=n->index;
      e->end2=nv->index;
      badde(b, e[0]);
      if(bn->index==0) cerr<<" hee in cond 11\n";
      swapedges(g.elist[ecut[0]].index, bn, &nv[0], bigg);
    }
    if(ecuts==2){
      cerr<<"cond 12\n";
      bnode **nv=new bnode*[3];
      for(int i=0; i<3; i++){
	nv[i]=new bnode[1];
	nv[i]->degree=0;
	nv[i]->enodes=0;
	nv[i]->arcs=NULL;
	nv[i]->next=NULL;
	if(i==0){
	  nv[i]->head=1;
	}
	else{
	  nv[i]->head=0;
	}
	baddn(b, *nv[i]);
      }
      bedge **e=new bedge*[3];
      for(int i=0; i<3; i++){
	e[i]=new bedge[1];
      }
      e[0]->end1=n->index;
      e[0]->end2=nv[0]->index;
      e[0]->next=NULL;
      badde(b, *e[0]);
      for(int i=1; i<3; i++){
	e[i]->end1=nv[0]->index;
	e[i]->end2=nv[i]->index;
	e[i]->next=NULL;
	badde(b, *e[i]);
      }
      if(n->index==0) cerr<<" here in cond 12\n";
      for(int i=0; i<ecuts; i++){
	swapedges(g.elist[ecut[i]].index, n, nv[i+1], bigg);
      }
      delete []e;
      delete []nv;
    }
    if(ecuts > 2){
      cerr<<"cond 1 else\n";
      graph g0;
      g0.nodes=0;
      g0.edges=0;
      g0.nlist=NULL;
      g0.elist=NULL;
      int w=cuts;
      int ncuts=0, *ncut=NULL, newecuts=0, *newecut=NULL;
      
      bnode *nv=new bnode[1];
      
      nv->degree=0;
      nv->enodes=0;
      nv->arcs=NULL;
      nv->next=NULL;
      nv->head=1;
      baddn(b, nv[0]);
      bedge *e=new bedge[1];
      e->end1=n->index;
      e->end2=nv->index;
      badde(b, e[0]);
      if(n->index==0) cerr<<" here in cond 1 else\n";
      for(int i=0; i<ecuts; i++){
	swapedges(g.elist[ecut[i]].index, n, nv, bigg);
      }
      cerr<<n->arcs<<" n->arcs\n";
      splitgraph(ecuts, ecut, g, g0);
      //cerr<<"hello\n";
      delete []ecut;
      ecut=NULL;
      
      g0.width=bigg.width;
      onecut(g0, ncuts, ncut, ecuts, ecut, newecuts, newecut);
      
      split(bigg, g0, ncuts, ncut, ecuts, ecut, newecuts, newecut, nv, b);
      delete []ncut;
      delete []newecut;
      newecut=NULL;
      ncut=NULL;

      freegraph(g0);
   }
    if(ecuts1==1 ){
      //freegraph(g);
      cerr<<"cond 21\n";
      bnode *nv=new bnode[1];
      nv->degree=0;
      nv->enodes=0;
      nv->arcs=NULL;
      nv->next=NULL;
      nv->head=1;
      baddn(b, nv[0]);
      bedge *e=new bedge[1];
      e->end1=nn->index;
      e->end2=nv->index;
      badde(b, e[0]);
      if(nn->index==0) cerr<<" here in cond 21\n";
      swapedges(g.elist[ecut1[0]].index, nn, nv, bigg);
    }
    if(ecuts1==2 ){
      //freegraph(g);
      cerr<<"cond 22\n";
      bnode **nv=new bnode*[3];
      for(int i=0; i<3; i++){
	nv[i]=new bnode[1];
	nv[i]->degree=0;
	nv[i]->enodes=0;
	nv[i]->arcs=NULL;
	nv[i]->next=NULL;
	if(i==0){
	  nv[i]->head=1;
	}
	else{
	  nv[i]->head=0;
	}
	baddn(b, *nv[i]);
      }
      bedge **e=new bedge*[3];
      for(int i=0; i<3; i++){
	e[i]=new bedge[1];
      }
      e[0]->end1=nn->index;
      e[0]->end2=nv[0]->index;
      e[0]->next=NULL;
      badde(b, *e[0]);
      for(int i=1; i<3; i++){
	e[i]->end1=nv[0]->index;
	e[i]->end2=nv[i]->index;
	e[i]->next=NULL;
	badde(b, *e[i]);
      }
      if(nn->index==0) cerr<<" here in cond22\n";
      for(int i=0; i<ecuts1; i++){
	swapedges(g.elist[ecut1[i]].index, nn, nv[i+1], bigg);
      }
      delete []e;
      delete []nv;
    }
    if(ecuts1 >2){
      cerr<<"cond 2else\n";
      graph g0;
      g0.nodes=0;
      g0.edges=0;
      g0.nlist=NULL;
      g0.elist=NULL;
      int w=cuts;
      int newecuts=0, *newecut=NULL;

      bnode *nv=new bnode[1];
      cerr<<nv<<" nv\n";
      nv->degree=0;
      nv->enodes=0;
      nv->arcs=NULL;
      nv->next=NULL;
      nv->head=1;
      baddn(b, nv[0]);
      bedge *e=new bedge[1];
      cerr<<e<<" e\n";
      cerr<<nn<<" nn\n";
      cerr<<nn->arcs<<" arcs\n";
      e->end1=nn->index;
      e->end2=nv->index;
      badde(b, e[0]);
      cerr<<" after badde\n";
      cerr<<ecuts1<<" ecuts1\n";
      if(nn->index==0) cerr<<" here in cond 2else\n";
      for(int i=0; i<ecuts1; i++){
	swapedges(g.elist[ecut1[i]].index, nn, nv, bigg);
      }
      cerr<<"after swapedges\n";
      splitgraph(ecuts1, ecut1, g, g0);
      cerr<<"after splitgraph\n";
      //freegraph(g);
      delete []cut;
      delete []ecut1;
      cut=NULL, ecut1=NULL;
      
      g0.width=bigg.width;
      cerr<<"before onecut\n";
      onecut(g0, cuts, cut, ecuts1, ecut1, newecuts, newecut);
      cerr<<ecut1<<" ecut1\n";
      split(bigg, g0, cuts, cut, ecuts1, ecut1, newecuts, newecut, nv, b);
      delete []newecut;
      newecut=NULL;
      if(g0.nodes) freegraph(g0);
    }
  }

  cerr<<"hello\n";
  //freegraph(g);
  if(cut) delete []cut;
  if(ecut) delete []ecut;
  if(ecut1) delete []ecut1;
  cut=NULL, ecut=NULL, ecut1=NULL;
  cerr<<g.edges<<" hello\n";
  return;
}

void onesplit(graph &g, int &cuts, int* &cut, int &ecuts, 
	       int* &ecut, int &ecuts1, int* &ecut1)
{
  int splite=-1;
  for(int i=0; i<g.edges-1; i++){
    if(g.elist[i].end1==g.elist[g.edges-1].end1 
       && g.elist[i].end2==g.elist[g.edges-1].end2){
      splite=i;
      break;
    }
  }
  
  if(splite >= 0){
    cuts=2;
    cut=new int[cuts];
    cut[0]=g.elist[g.edges-1].end1;
    cut[1]=g.elist[g.edges-1].end2;
    
    ecuts=1;
    ecuts1=g.edges-2;
    ecut=new int[ecuts];
    ecut1=new int[ecuts1];
    
    ecut[0]=splite;

    int k=0;
    for(int i=0; i<g.edges-1; i++){
      if(i!= splite){
	ecut1[k]=i;
	k++;
      }
    }
  }
  else{
    onecut(g, cuts, cut, ecuts, ecut, ecuts1, ecut1);
  }
}
				  
void splitgraph(int ecuts, int *ecut, graph &g, graph &g0)
{
  int count, *temp=NULL;
  for(int i=0; i<g.nodes; i++){
    g.nlist[i].color=0;
  }
  g0.width=g.width;
  //cerr<<ecut<<" hello\n";
  for(int i=0; i<ecuts; i++){
    g.nlist[g.elist[ecut[i]].end1].color=1;
    g.nlist[g.elist[ecut[i]].end2].color=1;
  }
  //cerr<<"hello\n";
  g0.nodes=0;
  for(int i=0; i<g.nodes; i++){
    if(g.nlist[i].color==1){
      g0.nodes++;
    }
  }
  count=0;
  temp=new int[g0.nodes];
  g0.nlist=new node[g0.nodes];
  for(int i=0; i<g.nodes; i++){
    if(g.nlist[i].color==1){
      temp[count]=i;
      count++;
    }
  }
  sort(g0.nodes, temp);
  //cerr<<"hello\n";
  g0.edges=ecuts ;
  g0.elist=new edge[g0.edges];
  for(int i=0; i<g0.edges; i++){
    g0.elist[i].end1=g.elist[ecut[i]].end1;
    g0.elist[i].end2=g.elist[ecut[i]].end2;
    g0.elist[i].index=g.elist[ecut[i]].index;
  }
  count=ecuts;
  
  for(int i=0; i<g0.nodes; i++){
    g0.nlist[i].degree=0;
  }
  for(int i=0; i<g0.edges; i++){
    count=0;
    for(int j=0; j<g0.nodes; j++){
      if(g0.elist[i].end1==temp[j]){
	g0.elist[i].end1=j;
	g0.nlist[j].index=g.nlist[temp[j]].index;
	g0.nlist[j].cut=g.nlist[temp[j]].cut;
	g0.nlist[j].degree++;
	count++;
      }
      if(g0.elist[i].end2==temp[j]){
	g0.elist[i].end2=j;
	g0.nlist[j].index=g.nlist[temp[j]].index;
	g0.nlist[j].cut=g.nlist[temp[j]].cut;
	g0.nlist[j].degree++;
	count++;
      }
      if(count==2){
	break;
      }
    }
  }
  int j=0;
  for(int i=0; i<g0.nodes; i++){
    if(g0.nlist[i].degree >0){
      g0.nlist[i].adj=new int[g0.nlist[i].degree];
      j=0;
      for(int k=0; k<g0.edges; k++){
        if(g0.elist[k].end1 == i || g0.elist[k].end2 == i){
          g0.nlist[i].adj[j]=k;
	  //cerr<<g0.nlist[i].adj[j]<<" k\n";
          j++;
        }
      }
    }
  }
  delete []temp;

}
    
 

void  sort(int num, int *sorte)
{
   int i, j, t, temp;

     if (num <= 1)
         return;

     swap (sorte[0], sorte[(num - 1)/2], temp);
    
     i = 0;
     j = num;
     t = sorte[0];

     while (1) {
         do i++; while (i < num && sorte[i] < t);
         do j--; while (sorte[j] > t);
         if (j < i) break;
         swap (sorte[i], sorte[j], temp);
     }
    
     swap (sorte[0], sorte[j], temp);

     sort (j,sorte);
     sort (num-i,sorte + i);

 }

void  sort1(int num, int *sorte, int *weight)
{
   int i, j, t, temp;

     if (num <= 1)
         return;

     swap (sorte[0], sorte[(num - 1)/2], temp);
     swap (weight[0], weight[(num-1)/2], temp);
     i = 0;
     j = num;
     t = weight[0];

     while (1) {
         do i++; while (i < num && weight[i] < t);
         do j--; while (weight[j] > t);
         if (j < i) break;
         swap (sorte[i], sorte[j], temp);
	 swap (weight[i], weight[j], temp);
     }
    
     swap (sorte[0], sorte[j], temp);
     swap (weight[0], weight[j], temp);

     sort1 (j,sorte, weight);
     sort1 (num-i,sorte + i, weight +i);

 }

void  sort2(int num, int *sorte, double *weight)
{
   int i, j, temp;
   double temp1;
   double t;
   if (num <= 1)
     return;
   
   swap (sorte[0], sorte[(num - 1)/2], temp);
   swap (weight[0], weight[(num-1)/2], temp1);
   i = 0;
   j = num;
   t = weight[0];
   
   while (1) {
     do i++; while (i < num && weight[i] < t);
     do j--; while (weight[j] > t);
     if (j < i) break;
     swap (sorte[i], sorte[j], temp);
     swap (weight[i], weight[j], temp1);
   }
   
   swap (sorte[0], sorte[j], temp);
   swap (weight[0], weight[j], temp1);

   sort2 (j,sorte, weight);
   sort2 (num-i,sorte + i, weight+i);
   
}

void unionn(int end1, int end2, bnode *bnlist)
{
  bnode *n1, *n2;
  for(bnode *n=bnlist; n; n=n->next){
    if(n->index==end1){
      n1=n;
    }
    if(n->index==end2){
      n2=n;
    }
  }
  link(find(n1), find(n2));
}

void link(bnode *n1, bnode *n2)
{
  //cout<<"hi\n";
  if(n1->mark > n2->mark){
    n2->parent=n1;
  }
  else{
    n1->parent=n2;
    if(n1->mark == n2->mark){
      n2->mark++;
    }
  }
  //cout<<" end link\n";
}

bnode* find(bnode *n)
{
  bnode *temp;
  //cout<<"find\n";
  //cout<<n->parent<<" parent\n";
  //cout<<n<<" n\n";
  if(n->parent!= n){
    temp=n->parent;
    n->parent=find(temp);
  }
  //cout<<"end find\n";
  return n->parent;
}

void postdfs(bnode *v, bgraph &b)
{
  int want;
  bnode *w=NULL;
  bqueue *bq;
  v->head=1;
  
  for(alist *e=v->adj; e; e=e->next){
    want=e->be->end1 + e->be->end2 - v->index;
    for(bnode *n=b.nlist; n; n=n->next){
      if(n->index==want){
	w=n;
	break;
      }
    }
    if(w->head==0){
      //if(v->index==1670){
      //cerr<<want<<" visited next from 1670\n";
      //}
      //if(v->index==1665){
      //cerr<<want<<" visited next from 1665\n";
      //}

      postdfs(w, b);
    }
  }

  //cerr<<v->index<<" pdfs\n";
  bq=new bqueue[1];
  bq->bv=v;
  bq->next=NULL;
  
  if(b.head==NULL){
    b.head=bq;
    b.tail=bq;
  }
  else{
    b.tail->next=bq;
    b.tail=bq;
  }
}
 
void bwidth (bnode *bn, bgraph &b, graph &g)
{
  bedge *ee=NULL;
  //cerr<<bn->index<<"'s degree is "<<bn->degree<<"\n";
  if(bn->degree==2){
    cerr<<bn->index<<" error for this bnode\n";
    exit(-1);
  }
  if(bn->degree==1){
    int e=bn->arcs->index;
    ee=bn->adj->be;
    if(g.nlist[g.elist[e].end1].degree >1 
       && g.nlist[g.elist[e].end2].degree >1){
      ee->order=2;
      ee->ms=new int[2];
      ee->msdeg=new int[2];
      ee->ms[0]=g.elist[e].end1;
      ee->ms[1]=g.elist[e].end2;
      ee->msdeg[0]=1;
      ee->msdeg[1]=1;
    }
    else if(g.nlist[g.elist[e].end1].degree >1 
	    && g.nlist[g.elist[e].end2].degree <=1){
      ee->order=1;
      ee->ms=new int[ee->order];
      ee->msdeg=new int[ee->order];
      ee->ms[0]=g.elist[e].end1;
      ee->msdeg[0]=1;
    }
    else if(g.nlist[g.elist[e].end2].degree >1 
	    && g.nlist[g.elist[e].end1].degree <=1){
      ee->order=1;
      ee->ms=new int[ee->order];
      ee->msdeg=new int[ee->order];
      ee->ms[0]=g.elist[e].end2;
      ee->msdeg[0]=1;
    }
    else{
      ee->order=0;
    }
  }
  else{
    bedge *e1=NULL, *e2=NULL;
    for(alist *a=bn->adj; a; a=a->next){
      //cerr<<a->be->end1<<" bedge "<<a->be->end2<<"\n"; 
      if(a->be->color==0){
	ee=a->be;
      }
      if(a->be->color==1 && e1==NULL){
	e1=a->be;
      }
      if(a->be->color==1 && e1 != a->be){
	e2=a->be;
      }
    }
    if(ee==NULL) {
      cerr<<"error ee is null\n";
      exit(-1);
    }
    //cerr<<e1<<" e1 \n";
    //cerr<<e2<<" e2\n";
    //cerr<<ee->end1<<" ee "<<ee->end2<<"\n";
    if(e1->order==0 && e2->order==0){
      ee->order=0;
    }
    else if( e1->order!=0 && e2->order==0){
      ee->order=e1->order;
      ee->ms=new int[ee->order];
      ee->msdeg=new int[ee->order];
      for(int i=0; i<ee->order; i++){
	ee->ms[i]=e1->ms[i];
	ee->msdeg[i]=e1->msdeg[i];
      }
    }
    else if( e2->order!=0 && e1->order==0){
      ee->order=e2->order;
      ee->ms=new int[ee->order];
      ee->msdeg=new int[ee->order];
      for(int i=0; i<ee->order; i++){
	ee->ms[i]=e2->ms[i];
	ee->msdeg[i]=e2->msdeg[i];
      }
    }
    else{
      int count=0;
      for(int i=0;i<g.nodes; i++){
	g.nlist[i].color=0;
      }
      for(int i=0; i<e1->order; i++){
	g.nlist[e1->ms[i]].color+=e1->msdeg[i];
      }
      for(int i=0; i<e2->order; i++){
	g.nlist[e2->ms[i]].color+=e2->msdeg[i];
      }
      for(int i=0; i<g.nodes; i++){
	if(g.nlist[i].color != 0 && g.nlist[i].color != g.nlist[i].degree){
	  count++;
	}
      }
      
      
      ee->order=count;
      if(count > 0){
	ee->ms=new int[ee->order];
	ee->msdeg=new int[ee->order];
	count=0;
	
	for(int i=0; i<g.nodes; i++){
	  if(g.nlist[i].color != 0 && g.nlist[i].color != g.nlist[i].degree){
	    ee->ms[count]=i;
	    ee->msdeg[count]=g.nlist[i].color;
	    count++;
	  }
	}
	
	for(int i=0; i<e1->order; i++){
	  g.nlist[e1->ms[i]].color=0;
	}
	for(int i=0; i<e2->order; i++){
	  g.nlist[e2->ms[i]].color=0;
	}
      }
    }
  }
  ee->color=1;

  b.width=max(ee->order, b.width);

}

void fillin (bnode *bn, bgraph &b, graph &g, int &ct, int *v)
{
  bedge *ee=NULL;
  //cerr<<bn->index<<"'s degree is "<<bn->degree<<"\n";
  if(bn->degree==2){
    cerr<<bn->index<<" error for this bnode\n";
    exit(-1);
  }
  if(bn->degree==1){
    int e=bn->arcs->index;
    ee=bn->adj->be;
    if(g.nlist[g.elist[e].end1].degree >1 
	    && g.nlist[g.elist[e].end2].degree <=1){
      v[ct]=g.elist[e].end2;
      g.nlist[g.elist[e].end2].token=1;
      ct++;
    }
    else if(g.nlist[g.elist[e].end2].degree >1 
	    && g.nlist[g.elist[e].end1].degree <=1){
      v[ct]=g.elist[e].end1;
      g.nlist[g.elist[e].end1].token=1;
      ct++;
    }
  }
  else{
    bedge *e1=NULL, *e2=NULL;
    for(alist *a=bn->adj; a; a=a->next){
      //cerr<<a->be->end1<<" bedge "<<a->be->end2<<"\n"; 
      if(a->be->color==0){
	ee=a->be;
      }
      if(a->be->color==1 && e1==NULL){
	e1=a->be;
      }
      if(a->be->color==1 && e1 != a->be){
	e2=a->be;
      }
    }
    if(ee==NULL) {
      cerr<<"error ee is null\n";
      exit(-1);
    }
    //cerr<<e1<<" e1 \n";
    //cerr<<e2<<" e2\n";
    //cerr<<ee->end1<<" ee "<<ee->end2<<"\n";
    int count=0;
    for(int i=0;i<g.nodes; i++){
      g.nlist[i].color=0;
    }
    for(int i=0; i<e1->order; i++){
      g.nlist[e1->ms[i]].color+=e1->msdeg[i];
    }
    for(int i=0; i<e2->order; i++){
      g.nlist[e2->ms[i]].color+=e2->msdeg[i];
    }
    for(int i=0; i<g.nodes; i++){
      if(g.nlist[i].color != 0 && g.nlist[i].color == g.nlist[i].degree){
	v[ct]=i;
	g.nlist[i].token=1;
	ct++;
      }
    }
  }
  ee->color=1;
}
      
	



bnode* midcliquefinder(int &ecuts, int *&ecut, bnode *bn, bgraph &b, graph &g,
		       graph &bigg)
{
  //    2   0  This is what the structure should be
  //    |   |
  //3 - 1 - bn

  int c=0, *ec=NULL, *ec1=NULL, count, cc, c1=0, c2=0;
  int end=0;
  bnode **n=NULL, *r;
  
  //cerr<<bn->index<<" bn\n";
  for(int i=0; i<g.nodes; i++){
    g.nlist[i].color=0;
    if(g.nlist[i].cut==1){
      g.nlist[i].color=1;
      //cerr<<g.nlist[i].index<<" is a cut node\n";
    }
  }
  
  
  //cerr<<ecuts<<" ecuts "<<ecut<<"\n";
  for(int i=0; i<ecuts; i++){
    if(g.nlist[g.elist[ecut[i]].end1].color==1 &&
       g.nlist[g.elist[ecut[i]].end2].color==1){
      //cerr<<g.elist[ecut[i]].index<<" is a clique edge\n";
      c1++;
      c++;
    }
  }
  //cerr<<c<<" c and ecuts "<<ecuts<<"\n";
  if( c > 0){
    //cerr<<"hello\n";
    int *clique=new int[c];
    c=0;
    for(int i=0;i<ecuts; i++){
      if(g.nlist[g.elist[ecut[i]].end1].color==1 &&
	 g.nlist[g.elist[ecut[i]].end2].color==1){
	//cerr<<g.nlist[g.elist[ecut[i]].end1].index<<" and ";
	//cerr<<g.nlist[g.elist[ecut[i]].end2].index<<" yp\n";
	clique[c]=ecut[i];
	c++;
      }
    }
    
    int temp, flip=-1;
    if(ecuts==1){//onecut edge should go first before clique edges
      for(int i=0; i<c; i++){
	if(clique[i]==ecut[0]){
	  flip=i;
	}
      }
      swap(clique[0], clique[flip], temp);
    }
    
    for(int i=1; i<c-1; i++){
      if(g.elist[clique[i]].end1!= g.elist[clique[i-1]].end1 
	 && g.elist[clique[i]].end1!= g.elist[clique[i-1]].end2
	 && g.elist[clique[i]].end2!= g.elist[clique[i-1]].end2
	 && g.elist[clique[i]].end2!= g.elist[clique[i-1]].end1){
	flip=-1;
	for(int j=i+1; j<c; j++){
	  if(g.elist[clique[j]].end1== g.elist[clique[i-1]].end1
	     || g.elist[clique[j]].end1== g.elist[clique[i-1]].end2
	     || g.elist[clique[j]].end2== g.elist[clique[i-1]].end2
	     || g.elist[clique[j]].end2== g.elist[clique[i-1]].end1){
	    flip=j;
	    break;
	  }
	}
	//cerr<<flip<<" flip\n";
	if(flip <0){
	  break;
	}
	else{
	  swap(clique[i],clique[flip],temp);
	}  
      }
    }
    /*
      cerr<<" new set of clique edges\n";
      for(int i=0; i<c; i++){
      int dum=clique[i];
      cerr<<g.nlist[g.elist[dum].end1].index<<" and ";
      cerr<<g.nlist[g.elist[dum].end2].index<<" cedges\n";
      }
      
      if(ecuts==c1){
      cerr<<c1<<" ecuts used up\n";
      }
      */
    //cerr<<c<<" is the number of clique edges\n";
    
  
    if(c!=ecuts){
      //cerr<<"c==ecuts\n";
      n=new bnode*[2*c];
      for(int i=0; i<2*c; i++){
	n[i]=new bnode[1];
	n[i]->degree=0;
	n[i]->enodes=0;
	n[i]->arcs=NULL;
	n[i]->next=NULL;
	if(i==0){
	  n[i]->head=1;
	}
	else{
	  n[i]->head=0;
	}
	baddn(b, *n[i]);
	//cerr<<n[i]->index<<" added\n";
      }
      bedge **e=new bedge*[2*c];
      for(int i=0; i<2*c; i++){
	e[i]=new bedge[1];
      }
      e[0]->end1=bn->index;
      e[0]->end2=n[0]->index;
      //cerr<<e[0]->end1<<" bedge "<<e[0]->end2<<"\n";
      e[0]->next=NULL;
      badde(b, *e[0]);
      e[1]->end1=bn->index;
      e[1]->end2=n[1]->index;
      e[1]->next=NULL;
      badde(b, *e[1]);
      if(c > 1){
	count=2;
	for(int i=1; i<2*c-2; i+=2){
	  e[count]->end1=n[i]->index;
	  e[count]->end2=n[i+1]->index;
	  //cerr<<e[count]->end1<<" bedge "<<e[count]->end2<<"\n";
	  e[count]->next=NULL;
	  badde(b, *e[count]);
	  count++;
	  e[count]->end1=n[i]->index;
	  e[count]->end2=n[i+2]->index;
	  //cerr<<e[count]->end1<<" bedge "<<e[count]->end2<<"\n";
	  e[count]->next=NULL;
	  badde(b, *e[count]);
	  count++;
	}
      }
      ec=new int[ecuts-c1];
      count=0, cc=0;
      if(bn->index==0) cerr<<" here in midclique\n";
      for(int i=0; i<c; i++){
	//cerr<<bn->index<<" and "<<n[2*cc+1]->index<<"\n";
	swapedges(g.elist[clique[i]].index, bn, n[2*cc], bigg);
	cc++;
      }
      for(int i=0; i<ecuts; i++){
	if(g.nlist[g.elist[ecut[i]].end1].color!=1 ||
	   g.nlist[g.elist[ecut[i]].end2].color!=1){
	  swapedges(g.elist[ecut[i]].index, bn, n[2*c-1], bigg);
	}
      }
      //cerr<<bn->index<<" the rest "<<n[2*c-2]->index<<"\n";
      end=2*c-1;
      delete []e;
    }
    else if (c ==ecuts && c != 1){
      //cerr<<2*c-1<<" hello\n";
      n=new bnode*[2*c-2];
      for(int i=0; i<2*c-2; i++){
	n[i]=new bnode[1];
	n[i]->degree=0;
	n[i]->enodes=0;
	n[i]->arcs=NULL;
	n[i]->next=NULL;
	if(i==0){
	  n[i]->head=1;
	}
	else{
	  n[i]->head=0;
	}
	baddn(b, *n[i]);
	//cerr<<n[i]->index<<" added\n";
	//cerr<<b.nodes<<" b's nodes\n";
      }
      bedge **e=new bedge*[2*c-2];
      for(int i=0; i<2*c-2; i++){
	e[i]=new bedge[1];
      }
      e[0]->end1=bn->index;
      e[0]->end2=n[0]->index;
      e[0]->next=NULL;
      badde(b, *e[0]);
      e[1]->end1=bn->index;
      e[1]->end2=n[1]->index;
      e[1]->next=NULL;
      badde(b, *e[1]);
      if(c >2){
	count=2;
	for(int i=1; i<2*c-4 ; i+=2){
	  e[count]->end1=n[i]->index;
	  e[count]->end2=n[i+1]->index;
	  e[count]->next=NULL;
	  badde(b, *e[count]);
	  //cerr<<count<<" count1\n";
	  count++;
	  e[count]->end1=n[i]->index;
	  e[count]->end2=n[i+2]->index;
	  e[count]->next=NULL;
	  badde(b, *e[count]);
	  //cerr<<count<<" count2\n";
	  count++;
	}
      }
      
      //if(ecuts-c1 >0){
      ec=new int[ecuts-c1];
      //}
      
      count=0, cc=0;
      if(bn->index==0) cerr<<" here in midclique again\n";
      for(int i=0; i<c-1; i++){
	swapedges(g.elist[clique[i]].index, bn, n[2*cc], bigg);
	cc++;
      }
      swapedges(g.elist[clique[c-1]].index, bn, n[2*c-3], bigg);      
      end=-1;
      delete []e;
    }
    else{
      end=-1;
    }
    count=0;
    //cerr<<clique<<" clique\n";
    delete []clique;
    for(int i=0; i<ecuts; i++){
      if(g.nlist[g.elist[ecut[i]].end1].color==1 &&
	 g.nlist[g.elist[ecut[i]].end2].color==1){
      }
      else{
	ec[count]=ecut[i];
	count++;
      }
    }
  
    
    if(end >=0){
      r=n[end];
    }
    else{
      r=bn;
    }
    //cerr<<n<<" n\n";
    if(n) delete []n;
    ecuts-=c1;
    //cerr<<ecut<<" ecut\n";
    delete []ecut;
    ecut=ec;
    for(int i=0; i<g.nodes; i++){
      g.nlist[i].color=0;
    }
    //cerr<<r<<"\n";
    return r;
  }
  else{
    for(int i=0; i<g.nodes; i++){
      g.nlist[i].color=0;
    }
    return bn; 	
  }
}


bnode* cliquefinder(int &ecuts, int *&ecut, bnode *bn, bgraph &b, graph &g, 
		    graph &bigg)
{
  //   3   1       This is the desired structure
  //   |   |
  //   2 - 0 - bn

  int c=0, *ec=NULL, *ec1=NULL, count, cc, c1=0, c2=0;
  int end=0;
  bnode **n, *r;
  
  //cerr<<bn->index<<" bn\n";
  for(int i=0; i<g.nodes; i++){
    g.nlist[i].color=0;
    if(g.nlist[i].cut==1){
      g.nlist[i].color=1;
      //cerr<<g.nlist[i].index<<" is a cut node\n";
    }
  }
  
  
  //cerr<<ecuts<<" ecuts "<<ecut<<"\n";
  for(int i=0; i<ecuts; i++){
    if(g.nlist[g.elist[ecut[i]].end1].color==1 &&
       g.nlist[g.elist[ecut[i]].end2].color==1){
      //cerr<<g.elist[ecut[i]].index<<" is a clique edge\n";
      c1++;
      c++;
    }
  }
  if( c > 0){
    int *clique=new int[c];
    c=0;
    for(int i=0;i<ecuts; i++){
      if(g.nlist[g.elist[ecut[i]].end1].color==1 &&
	 g.nlist[g.elist[ecut[i]].end2].color==1){
	//cerr<<g.nlist[g.elist[ecut[i]].end1].index<<" and ";
	//cerr<<g.nlist[g.elist[ecut[i]].end2].index<<" yp\n";
	clique[c]=ecut[i];
	c++;
      }
    }
    
    int temp, flip;
    if(ecuts==1){//onecut edge should go first before clique edges
      for(int i=0; i<c; i++){
	if(clique[i]==ecut[0]){
	  flip=i;
	}
      }
      swap(clique[0], clique[flip], temp);
    }
    
    for(int i=1; i<c-1; i++){
      if(g.elist[clique[i]].end1!= g.elist[clique[i-1]].end1 
	 && g.elist[clique[i]].end1!= g.elist[clique[i-1]].end2
	 && g.elist[clique[i]].end2!= g.elist[clique[i-1]].end2
	 && g.elist[clique[i]].end2!= g.elist[clique[i-1]].end1){
	flip=-1;
	for(int j=i+1; j<c; j++){
	  if(g.elist[clique[j]].end1== g.elist[clique[i-1]].end1
	     || g.elist[clique[j]].end1== g.elist[clique[i-1]].end2
	     || g.elist[clique[j]].end2== g.elist[clique[i-1]].end2
	     || g.elist[clique[j]].end2== g.elist[clique[i-1]].end1){
	    flip=j;
	    break;
	  }
	}
	//cerr<<flip<<" flip\n";
	if(flip <0){
	  break;
	}
	else{
	  swap(clique[i],clique[flip],temp);
	}  
      }
    }
    /*
      cerr<<" new set of clique edges\n";
      for(int i=0; i<c; i++){
      int dum=clique[i];
      cerr<<g.nlist[g.elist[dum].end1].index<<" and ";
      cerr<<g.nlist[g.elist[dum].end2].index<<" cedges\n";
      }
      
      if(ecuts==c1){
      cerr<<c1<<" ecuts used up\n";
      }
      */
    //cerr<<c<<" is the number of clique edges\n";
    
  
     if(c!=ecuts){
      //cerr<<"c==ecuts\n";
      n=new bnode*[2*c];
      for(int i=0; i<2*c; i++){
	n[i]=new bnode[1];
	n[i]->degree=0;
	n[i]->enodes=0;
	n[i]->arcs=NULL;
	n[i]->next=NULL;
	if(i==0){
	  n[i]->head=1;
	}
	else{
	  n[i]->head=0;
	}
	baddn(b, *n[i]);
	//cerr<<n[i]->index<<" added\n";
      }
      bedge **e=new bedge*[2*c];
      for(int i=0; i<2*c; i++){
	e[i]=new bedge[1];
      }
      e[0]->end1=bn->index;
      e[0]->end2=n[0]->index;
      //cerr<<e[0]->end1<<" bedge "<<e[0]->end2<<"\n";
      e[0]->next=NULL;
      badde(b, *e[0]);
      count=1;
      for(int i=0; i<2*c-3; i+=2){
	e[count]->end1=n[i]->index;
	e[count]->end2=n[i+1]->index;
	//cerr<<e[count]->end1<<" bedge "<<e[count]->end2<<"\n";
	e[count]->next=NULL;
	badde(b, *e[count]);
	count++;
	e[count]->end1=n[i]->index;
	e[count]->end2=n[i+2]->index;
	//cerr<<e[count]->end1<<" bedge "<<e[count]->end2<<"\n";
	e[count]->next=NULL;
	badde(b, *e[count]);
	count++;
      }
      e[count]->end1=n[2*c-2]->index;
      e[count]->end2=n[2*c-1]->index;
      //cerr<<e[count]->end1<<" bedge "<<e[count]->end2<<"\n";
      e[count]->next=NULL;
      badde(b, *e[count]);
      
      
      ec=new int[ecuts-c1];
      count=0, cc=0;
      if(bn->index==0) cerr<<" here in cliquefinder\n";
      for(int i=0; i<c; i++){
	//cerr<<bn->index<<" and "<<n[2*cc+1]->index<<"\n";
	swapedges(g.elist[clique[i]].index, bn, n[2*cc+1], bigg);
	cc++;
      }
      for(int i=0; i<ecuts; i++){
	if(g.nlist[g.elist[ecut[i]].end1].color!=1 ||
	   g.nlist[g.elist[ecut[i]].end2].color!=1){
	  swapedges(g.elist[ecut[i]].index, bn, n[2*c-2], bigg);
	}
      }
      //cerr<<bn->index<<" the rest "<<n[2*c-2]->index<<"\n";
      end=2*c-2;
      delete []e;
    }
    else{
      //cerr<<2*c-1<<" hello\n";
      n=new bnode*[2*c-1];
      for(int i=0; i<2*c-1; i++){
	n[i]=new bnode[1];
	n[i]->degree=0;
	n[i]->enodes=0;
	n[i]->arcs=NULL;
	n[i]->next=NULL;
	if(i==0){
	  n[i]->head=1;
	}
	else{
	  n[i]->head=0;
	}
	baddn(b, *n[i]);
	//cerr<<n[i]->index<<" added\n";
	//cerr<<b.nodes<<" b's nodes\n";
      }
      bedge **e=new bedge*[2*c-1];
      for(int i=0; i<2*c-1; i++){
	e[i]=new bedge[1];
      }
      e[0]->end1=bn->index;
      e[0]->end2=n[0]->index;
      e[0]->next=NULL;
      badde(b, *e[0]);
      if(2*c-1 >1){
	count=1;
	for(int i=0; i<2*c-3 ; i+=2){
	  e[count]->end1=n[i]->index;
	  e[count]->end2=n[i+1]->index;
	  e[count]->next=NULL;
	  badde(b, *e[count]);
	  //cerr<<count<<" count1\n";
	  count++;
	  e[count]->end1=n[i]->index;
	  e[count]->end2=n[i+2]->index;
	  e[count]->next=NULL;
	  badde(b, *e[count]);
	  //cerr<<count<<" count2\n";
	  count++;
	}
      }
      
      
      //if(ecuts-c1 >0){
      ec=new int[ecuts-c1];
      //}
      if(bn->index==0) cerr<<" here in cliquefinder again\n";
      count=0, cc=0;
      for(int i=0; i<c-1; i++){
	swapedges(g.elist[clique[i]].index, bn, n[2*cc+1], bigg);
	cc++;
      }
      swapedges(g.elist[clique[c-1]].index, bn, n[2*c-2], bigg);      
      end=-1;
      delete []e;
    }
      
    count=0;
    delete []clique;
    for(int i=0; i<ecuts; i++){
      if(g.nlist[g.elist[ecut[i]].end1].color==1 &&
	 g.nlist[g.elist[ecut[i]].end2].color==1){
      }
      else{
	ec[count]=ecut[i];
	count++;
      }
    }
  
    
    if(end >=0){
      r=n[end];
    }
    else{
      r=bn;
    }
    delete []n;
    ecuts-=c1;
    delete []ecut;
    ecut=ec;
    for(int i=0; i<g.nodes; i++){
      g.nlist[i].color=0;
    }
    return r;
  }
  else{
    for(int i=0; i<g.nodes; i++){
      g.nlist[i].color=0;
    }
    return bn;
  }
}

void bigcliquefinder(int &ecuts, int *&ecut, int &ecuts1, int *&ecut1,
		     bnode *bn, bgraph &b, graph &g, graph &bigg)
{
  bnode **n= new bnode*[3];
  bedge *be;
  int c=0, cc=0;
  int *e;
  //for(int i=0; i<g.nodes; i++){
  //g.nlist[i].cut=1;
  //g.nlist[i].color=0;
  //}

  for(int i=0; i<g.nodes; i++){
    g.nlist[i].cut=1;
    g.nlist[i].color=0;
    if(i%3 == 1){
      g.nlist[i].color=1;
      c++;
    }
    if(i%3 == 2){
      g.nlist[i].color=2;
      cc++;
    }
  }
  //cerr<<c<<" 1's and 2's "<<cc<<"\n";
  c=0;
  //for(int i=0; i< g.edges; i++){
  //g.elist[i].wk=0;
  //}
  int ce=0, ce1=0, ce2=0;
  //if(g.nodes > 3){
  for(int i=0; i < g.edges; i++){
    g.elist[i].wk=0;
    if((g.nlist[g.elist[i].end1].color==0 || g.nlist[g.elist[i].end1].color==2)
       &&(g.nlist[g.elist[i].end2].color==2 
	  || g.nlist[g.elist[i].end2].color==0)){
      g.elist[i].wk=1;
      ce1++;
      //cerr<<g.elist[i].end1<<" 2 "<<g.elist[i].end2<<"\n";
    }
    if((g.nlist[g.elist[i].end1].color==1 || g.nlist[g.elist[i].end1].color==2)
       &&(g.nlist[g.elist[i].end2].color==2 
	  || g.nlist[g.elist[i].end2].color==1) && g.elist[i].wk==0){
      g.elist[i].wk=2;
      ce2++;
      //cerr<<g.elist[i].end1<<" 2 "<<g.elist[i].end2<<"\n";
    }
  }
  /* for(int i=0; i < g.edges; i++){
    if(g.elist[i].wk==0 && (g.nlist[g.elist[i].end1].color==1 
			    ||g.nlist[g.elist[i].end2].color==1)){
      g.elist[i].wk=1;
      ce1++;
      //cerr<<g.elist[i].end1<<" 1 "<<g.elist[i].end2<<"\n";
    }
  }*/
  ce=g.edges-ce1-ce2;
  if(ce==0 || ce1==0 || ce2==0){
    cerr<<"somebody is zero "<<ce<<" ce "<<ce1<<" ce1 "<<ce2<<" ce2\n";
    exit(-1);
  }
  //}
  //else{
  //for(int i=0; i<g.edges; i++){
  //  g.elist[i].wk=i;
  //}
  //}

  for(int i=0; i<3; i++){
    c=0;
    n[i]=new bnode[1];
    be=new bedge[1];
    n[i]->degree=0;
    n[i]->enodes=0;
    n[i]->arcs=NULL;
    n[i]->next=NULL;
    n[i]->head=0;
    baddn(b, *n[i]);
    be->end1=bn->index;
    be->end2=n[i]->index;
    be->next=NULL;
    badde(b, *be);
    if(bn->index==0) cerr<<" here in bigcliquefinder\n";
    for(int j=0; j<g.edges; j++){
      if(g.elist[j].wk==i){
	swapedges(g.elist[j].index, bn, n[i], bigg);
	c++;
      }
    }
    if(c >1){
      e=new int[c];
      c=0;
      for(int j=0; j<g.edges; j++){
	if(g.elist[j].wk==i){
	  e[c]=j;
	  c++;
	}
      }
      midcliquefinder(c, e, n[i], b, g, bigg);
      e=NULL;
    }
  }
  

  
  
  delete []n;
}
  
void blink(int e, int ee, graph &g, bgraph &b)
{

  bedge *be=new bedge[1];

  be->end1=g.elist[e].holder->index;
  be->end2=g.elist[ee].holder->index;
  //cerr<<be->end1<<" be "<<be->end2<<"\n";
  badde(b, be[0]);

  if(g.elist[e].holder->degree >1){
    bnode *n=new bnode[1];
    baddn(b, n[0]);

    bedge *bv=new bedge[1];
    bv->end1=g.elist[e].holder->index;
    bv->end2=n->index;
    badde(b, bv[0]);
    
    swapedges(e, g.elist[e].holder, n, g);
  }

  if(g.elist[ee].holder->degree >1){
    bnode *nn=new bnode[1];
    baddn(b, nn[0]);

    bedge *bvv=new bedge[1];
    bvv->end1=g.elist[ee].holder->index;
    bvv->end2=nn->index;
    badde(b, bvv[0]);
    
    swapedges(ee, g.elist[ee].holder, nn, g);
  }

}
  
  

  


  
  
      


