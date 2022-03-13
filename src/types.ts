export class TolNode {
	name: string;
	children: TolNode[];
	constructor(name: string, children: TolNode[] = []){
		this.name = name;
		this.children = children;
	}
}
export class TreeNode {
	tolNode: TolNode;
	children: TreeNode[];
	x: number;
	y: number;
	w: number;
	h: number;
	headerSz: number;
	sepSweptArea: SepSweptArea | null;
	tileCount: number;
	constructor(tolNode: TolNode, children: TreeNode[], x=0, y=0, w=0, h=0,
		{headerSz=0, sepSweptArea=null, tileCount=1} = {}){
		this.tolNode = tolNode;
		this.children = children;
		this.x = x;
		this.y = y;
		this.w = w;
		this.h = h;
		this.headerSz = headerSz;
		this.sepSweptArea = sepSweptArea;
		this.tileCount = tileCount;
	}
}
export class LayoutNode {
	name: string;
	children: LayoutNode[];
	x: number;
	y: number;
	w: number;
	h: number;
	headerSz: number;
	contentW: number;
	contentH: number;
	empSpc: number;
	sepSweptArea: SepSweptArea | null;
	constructor(name: string, children: LayoutNode[], x=0, y=0, w=0, h=0,
		{headerSz=0, contentW=0, contentH=0, empSpc=0, sepSweptArea=null as SepSweptArea|null} = {}){
		this.name = name;
		this.x = x;
		this.y = y;
		this.w = w;
		this.h = h;
		this.headerSz = headerSz;
		this.children = children;
		this.contentW = contentW;
		this.contentH = contentH;
		this.empSpc = empSpc;
		this.sepSweptArea = sepSweptArea;
	}
}
export class SepSweptArea {
	x: number;
	y: number;
	w: number;
	h: number;
	sweptLeft: boolean;
	tileSpacing: number;
	constructor(x: number, y: number, w: number, h: number, sweptLeft: boolean, tileSpacing: number){
		this.x = x;
		this.y = y;
		this.w = w;
		this.h = h;
		this.sweptLeft = sweptLeft;
		this.tileSpacing = tileSpacing;
	}
}
