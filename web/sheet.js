import {app} from '../../scripts/app.js';
import {api} from '../../scripts/api.js';
import {createExtension} from './reference13_integration.js';
for(const name of ['style.css','reference13_style.css']){const l=document.createElement('link');l.rel='stylesheet';l.href=new URL(name,import.meta.url);document.head.append(l);}
app.registerExtension(createExtension(app,api));
