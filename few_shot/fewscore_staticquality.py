import argparse
import os
from openai import OpenAI
import openai
from tool import videoreader

MODEL="gpt-4o-2024-08-06"

parser = argparse.ArgumentParser()
parser.add_argument(
    "--dimension",
    type=str,
    default="imaging_quality",
    choices=["imaging_quality", "aesthetic_quality"],
)
args = parser.parse_args()

# 创建一个OpenAI客户端实例
client = OpenAI(
    api_key="",
    base_url=""  # 替换为你的自定义API域
)

dimension = args.dimension
from PromptTemplate4GPTeval import Prompt4ImagingQuality
prompt_template = Prompt4ImagingQuality

import json

data_prepath = ''
with open("./Human_anno/{}.json".format(dimension)) as f:
    human_anno = json.load(f)



batch_stpath = '../batch_api/{}'.format(dimension)
if not os.path.exists(batch_stpath):
    os.makedirs(batch_stpath)

batch_unique_ids = []
batch_split_ids = []

def eval_batch_onebyone(index_list,batch_id):
    print("Thread {} is running".format(batch_id))
    model2message = {
    'cogvideox5b':"12 frames from cogvideox5b,which you need to evaluate \n",
    'kling':"10 frames from kling ,which you need to evaluate\n ", 
    'gen3': "20 frames from gen3 ,which you need to evaluate\n",
    'videocrafter2':"4 frames from videocrafter2,which you need to evaluate",
    'pika':"7 frames from pika ,which you need to evaluate",
    'show1':"8 frames from show1,which you need to evaluate ",
    'lavie':"5 frames from lavie ,which you need to evaluate",
    }
    requests = []
    for key, value in model2message.items():
        modelname = key
        modelmessage = value
   
        for i in index_list:     
            request ={"custom_id": "request-{}-{}".format(i,modelname), 
                    "method": "POST", 
                    "url": "/v1/chat/completions",
                    "body": {"model": MODEL,
                                "messages": [],
                                "temperature": 0}}

            examplemodels = [x for x in model2message.keys() if x != modelname]
            frames = videoreader.process_video(data_prepath,human_anno[i]['videos'],1)


            prompten = human_anno[i]['prompt_en']
            # question = human_anno[i]['question_en']
            # subject = human_anno[i]['subject_en']
            # scene = human_anno[i]['scene_en']
            # objet = human_anno[i]['object']
            messages=[
            {
            "role": "system", "content":
                prompt_template
                }
                ,
            {
                "role": "user", "content":[
           "According to **Important Notes** in system meassage, there are examples from other models.\n",
            *[item for examplemodel in examplemodels for item in [
                "This example is from model {} \n".format(examplemodels.index(examplemodel)+1),
                {"type": "image_url", "image_url": {"url": f'data:image/jpg;base64,{frames[examplemodel][0]}', "detail": "low"}}
            ]],              
            
            "These are the frames from the video you are evaluating. \n",
                *map(lambda x: {"type": "image_url", 
                    "image_url": {"url": f'data:image/jpg;base64,{x}', "detail": "low"}},frames[modelname]),    

            "Assuming there are a video ' scoring 'x',provide your analysis and explanation in the output format as follows:\n"
            "- video: x ,because ..."
              ],
                }
            ]
            request['body']['messages'] = messages
            requests.append(request)

    with open(os.path.join(batch_stpath,"requests_{}_batch_{}.jsonl".format(dimension,batch_id)), "w") as f:
        for entry in requests:
            json_line = json.dumps(entry)
            f.write(json_line + '\n')
    
    batch_input_file = client.files.create(
             file=open(os.path.join(batch_stpath,"requests_{}_batch_{}.jsonl".format(dimension,batch_id)), "rb"),
              purpose="batch"
             )

    batch_input_file_id = batch_input_file.id    

    batch_object = client.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
            "description": "nightly group1 {} eval job batch {}".format(dimension,batch_id)
            }
                                        )
    
    batch_split_ids.append(batch_id)
    batch_unique_ids.append(batch_object.id)

    print("Thread {} is done".format(batch_id))



ls = list(range(0,len(human_anno)))


import threading

batch_size = 5
batches = [ls[i:i + batch_size] for i in range(0, len(ls), batch_size)]

# with open("./batch_infos/batch_info_{}.json".format(dimension), "r") as f:
#     batch_info = json.load(f)

# batch_split_ids = batch_info['batch_split_ids']
# batches = batch_info['videos_in_batch']

threads = []
for i, batch in enumerate(batches):
    thread = threading.Thread(target=eval_batch_onebyone, args=(batch, i))
    threads.append(thread)
    thread.start()

print("All threads started")
# 等待所有线程完成
for thread in threads:
    thread.join()

#保存batch信息
with open("./batch_infos/batch_info_{}.json".format(dimension), "w") as f:
    json.dump({"batch_unique_ids": batch_unique_ids, "batch_split_ids": batch_split_ids,"videos_in_batch":batches}, f, indent=4)


with open("./batch_infos/batch_info_{}.json".format(dimension), "r") as f:
    batch_info = json.load(f)

    
batchids = batch_info["batch_unique_ids"]
llmeval_path = "./GPT4o_eval_results/{}/{}_llmeval.json".format(dimension,dimension)

with open(llmeval_path, "r") as f:
    llmeval = json.load(f)
    
for i in ls:
    if str(i) not in llmeval.keys():
         llmeval[str(i)] = {}

for id in batchids:
    batch_object = client.batches.retrieve(id)
    print("id:{} status:{} descrepition:{}".format(id,batch_object.status,batch_object.metadata['description']))

    if batch_object.status != "completed":
        print("batch {} is not completed".format(id))
        continue    

    file_response = client.files.content(batch_object.output_file_id)
    for line in file_response.text.splitlines():
        index = json.loads(line)["custom_id"].split("-")[-2]
        model = json.loads(line)["custom_id"].split("-")[-1]

        # index = json.loads(line)["custom_id"].split("-")[-1]

        eval_res = json.loads(line)["response"]["body"]["choices"][0]["message"]["content"].replace('\n\n','\n')
        
        llmeval[index][model] = eval_res
        # llmeval[index] = eval_res
    with open(llmeval_path, "w") as f:
        
        json.dump(llmeval, f, indent=4)

    print("batch {} done,end index {}".format(id,index))