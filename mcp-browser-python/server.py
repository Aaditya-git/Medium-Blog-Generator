#!/usr/bin/env python3
import json, sys, pathlib
from playwright.sync_api import sync_playwright
def send(o): print(json.dumps(o)); sys.stdout.flush()
def respond(i,r): send({'jsonrpc':'2.0','id':i,'result':r})
def main():
    for l in sys.stdin:
        m=json.loads(l); rid=m.get('id'); method=m.get('method')
        if method=='initialize':
            respond(rid,{'protocolVersion':'2024-11-05','serverInfo':{'name':'browser-mcp-python','version':'1.0'},'capabilities':{'tools':{}}})
            send({'jsonrpc':'2.0','method':'notifications/ready','params':{'capabilities':{'tools':{}}}}); continue
        if method=='tools/list':
            respond(rid,{'tools':[{'name':'medium.publish_from_folder','description':'Publish Medium draft','inputSchema':{'type':'object','properties':{'folder':{'type':'string'}},'required':['folder']}}]}); continue
        if method=='tools/call':
            folder=m['params']['arguments']['folder']
            try:
                with sync_playwright() as p:
                    b=p.chromium.launch(headless=False)
                    c=b.new_context(); pg=c.new_page()
                    pg.goto('https://medium.com/new-story',wait_until='load')
                    pg.keyboard.type('Demo Title'); pg.keyboard.press('Enter')
                    pg.keyboard.type('\\nDemo body'); pg.wait_for_timeout(1000)
                    url=pg.url; b.close()
                respond(rid,{'content':[{'type':'text','text':json.dumps({'ok':True,'url':url})}],'isError':False})
            except Exception as e:
                respond(rid,{'content':[{'type':'text','text':json.dumps({'ok':False,'error':str(e)})}],'isError':True})
if __name__=='__main__': main()
