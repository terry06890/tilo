export class TolNode {
	name: string;
	children: TolNode[];
	constructor(name: string, children: TolNode[]){
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
	sideArea: SideArea | null;
	tileCount: number;
	constructor(tolNode: TolNode, children: TreeNode[], x=0, y=0, w=0, h=0, 
		{headerSz=0, sideArea=null, tileCount=1} = {}){
		this.tolNode = tolNode;
		this.children = children;
		this.x = x;
		this.y = y;
		this.w = w;
		this.h = h;
		this.headerSz = headerSz;
		this.sideArea = sideArea;
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
	sideArea: SideArea | null;
	constructor(name: string, children: LayoutNode[], x=0, y=0, w=0, h=0, 
		{headerSz=0, contentW=0, contentH=0, empSpc=0, sideArea=null as SideArea|null} = {}){
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
		this.sideArea = sideArea;
	}
}
export class SideArea {
	x: number;
	y: number;
	w: number;
	h: number;
	sweptLeft: boolean;
	extraSz: number;
	constructor(x: number, y: number, w: number, h: number, sweptLeft: boolean, extraSz: number){
		this.x = x;
		this.y = y;
		this.w = w;
		this.h = h;
		this.sweptLeft = sweptLeft;
		this.extraSz = extraSz;
	}
}
export class LeftoverArea {
	parentX: number;
	parentY: number;
	w: number;
	h: number;
	sweptLeft: boolean;
	constructor(parentX: number, parentY: number, w: number, h: number, sweptLeft: boolean){
		this.parentX = parentX;
		this.parentY = parentY;
		this.w = w;
		this.h = h;
		this.sweptLeft = sweptLeft;
	}
}
