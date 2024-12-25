import os.path as osp
from glob import glob
from datetime import datetime
import pysubs2
import json

# some element IDs
winID = "com.blackmagicdesign.resolve.BuildTimelineScript"	# should be unique for single instancing
execID = "Exec"
refreshID = "Refresh"
sourceID = "SourcePath"
fileID = "File"
timelineID = "Timeline"
expswitchID = "ExportEnable"
targetID = "TargetPath"
logID = "Log"
config_filename = 'C:\\Users\\Public\\Documents\\davinci_plugin_save.json'

def save_global_config(config):
    json.dump(config, open(config_filename, 'w'), indent=2)

def load_global_config():
    try:
        global_config = json.load(open(config_filename, 'r'))
    except:
        global_config = {
            'video_type': '.mkv',
            'subtitle_type': '.srt',
            'import_dir': 'D:\\Video2024',
            'export_dir': 'E:\\SynologyDrive\\PaperReview\\Final',
        }
        save_global_config(global_config)
    return global_config

global_config = load_global_config()
try:
    video_type = global_config['video_type']
    subtitle_type = global_config['subtitle_type']
except:
    video_type = '.mkv'
    subtitle_type = '.srt'

ui = fusion.UIManager
dispatcher = bmd.UIDispatcher(ui)

resolve = app.GetResolve()
ms = resolve.GetMediaStorage()
projectManager = resolve.GetProjectManager()

# check for existing instance
win = ui.FindWindow(winID)
if win:
	win.Show()
	win.Raise()
	exit()
	
# otherwise, we set up a new window, with HTML header (using the Examples logo.png)
# logoPath = fusion.MapPath(r"AllData:Scripts/Comp/SamplePlugin/img/logo.png")
header = '<html><body><h1 style="vertical-align:middle;">'
# header = header + '<img src="' + logoPath + '"/>&nbsp;&nbsp;&nbsp;'
header = header + '<b>Build Timeline from Subtitle</b>'
header = header + '</h1></body></html>'

# define the window UI layout
win = dispatcher.AddWindow({
	'ID': winID,
	# 'Geometry': [ 100,100,600,300 ],
	'WindowTitle': "Build Timeline from Subtitle",
	},
	ui.VGroup([
		ui.Label({ 'Text': header, 'Weight': 0, 'Font': ui.Font({ 'Family': "Times New Roman" }) }),
		# ui.Label({ 'Text': "Workflow script", 'Weight': 0, 'Font': ui.Font({ 'Family': "Times New Roman", 'PixelSize': 12 }) }),
        ui.HGroup({ 'Weight': 0, }, [
            ui.Label({'Text': 'Video and subtitle path: ', 'Weight': 0}),
            ui.LineEdit({
			'ID': sourceID,
            'Weight': 5
			}),
			ui.HGap(2),
			ui.Button({ 'ID': refreshID, 'Text': "Refresh" }),
			]),

        ui.HGroup({ 'Weight': 0, }, [
            ui.Label({'Text': 'File to add: ', 'Weight': 0}),
            ui.ComboBox({
                'ID': fileID,
                'Weight': 5
            })
        ]),
        ui.HGroup({ 'Weight': 0, }, [
            ui.Label({'Text': 'Target timeline: ', 'Weight': 0}),
            ui.LineEdit({
                'ID': timelineID,
                'Weight': 5
            })
        ]),
        ui.HGroup({ 'Weight': 0, }, [
            ui.CheckBox({'Text': 'Export subs', 'ID': expswitchID, 'Checked': True}),
            ui.Label({'Text': 'Target path: ', 'Weight': 0}),
            ui.LineEdit({
                'ID': targetID,
                'Weight': 5
            })
        ]),
        ui.Button({ 'ID': execID,  'Text': "Build Timeline" }),
        ui.TextEdit({
			'ID': logID,
            'Weight': 5,
            'ReadOnly': True
			}),
	])
)
   

def log_print(text):
    text = str(text)
    print(text)
    log = win.Find(logID)
    tl = log.PlainText.split('\n')
    tl.append(text)
    limit = 50
    if len(tl) > limit:
        tl = tl[-limit:]
    log.PlainText = '\n'.join(tl)

    
def getAllTimelines():
    project = projectManager.GetCurrentProject()
    
    # get names of all timelines
    return {project.GetTimelineByIndex(i + 1).GetName(): project.GetTimelineByIndex(i + 1) for i in range(project.GetTimelineCount())}
    

def merge_close_subtitles(subs, threshold=500):
    """
    Merges subtitles that are close to each other.
    :param subs: A pysubs2 SSAFile object containing subtitles.
    :param threshold: The maximum gap (in milliseconds) between subtitles to consider for merging.
    """
    i = 0
    while i < len(subs) - 1:
        if subs[i+1].start - subs[i].end <= threshold:
            subs[i].end = subs[i+1].end
            del subs[i+1]
        else:
            i += 1
    return subs


def compress_subtitles(subs, video_length, output_subtitle_path):
    n = len(subs)
    
    if n == 0:
        log_print('No subtitle found')
        return
    
    for i in range(n):
        # Adjust the start of the next subtitle to immediately follow the current one
        if i == 0:
            diff = subs[i].start
        else:
            diff = subs[i].start - subs[i - 1].end - 1
        subs[i].start -= diff
        subs[i].end -= diff
    sd = subs[-1].end / 1000
    log_print(f'Subtitle vs Video length: {sd:.3f} vs {video_length:.3f}, timestamps aligned.')
    
    ratio = video_length / sd
    for i in range(n):
        subs[i].start *= ratio
        subs[i].end *= ratio
    # Save the adjusted subtitles
    subs.save(output_subtitle_path)
    log_print('Compressed subs exported to ' + output_subtitle_path)


def OnExec(ev):
	# import file
    if win.Find(fileID).Count == 0:
        log_print('Please select a file to import')
        return
    
    log_print('-' * 10 + 'Build Timeline Started' + '-' * 10)
    
    # add video file to media pool
    file_base = win.Find(fileID).CurrentText
    ms.AddItemListToMediaPool(file_base + video_type)

    # get names ready
    _, file_name = osp.split(file_base)
    full_file_name = file_name + video_type
    timeline_name = win.Find(timelineID).Text
    # log_print(f'{full_file_name = } {timeline_name = }')

    # find the clip items (media pool item)
    project = projectManager.GetCurrentProject()
    mediaPool = project.GetMediaPool()
    rootFolder = mediaPool.GetRootFolder()
    clips = rootFolder.GetClipList()
    
    for clip in clips:
        if clip.GetClipProperty('Clip Name') == full_file_name:
            break
    
    # prepare the clip to insert
    subtitle_path = file_base + subtitle_type
    subs = pysubs2.load(subtitle_path)
    # log_print(clip.GetClipProperty())
    fps = clip.GetClipProperty('FPS')
    log_print(f'Clip FPS: {fps}' )
    subClipList = []    
    for sub in merge_close_subtitles(subs):
        start = sub.start / 1000.0  # Convert milliseconds to seconds
        end = sub.end / 1000.0
        subClipList.append({
            "mediaPoolItem": clip,
            "startFrame": int(start * fps),
            "endFrame": int(end * fps),
        })
    if len(subClipList) == 0:
        log_print('No clip founded, exit')
        return
    # find the timeline to insert
    timelines = getAllTimelines()
    if timeline_name in timelines:
        target_timeline = timelines[timeline_name]
        project.SetCurrentTimeline(target_timeline)
        mediaPool.AppendToTimeline(subClipList)
    else:
        # for unknown reasons it will not create multiple clips
        # when dumping the whole list to the following function
        target_timeline = mediaPool.CreateTimelineFromClips(timeline_name, subClipList[:1]) 
        project.SetCurrentTimeline(target_timeline)
        mediaPool.AppendToTimeline(subClipList[1:])
    # log_print(target_timeline.GetSetting()) # thisline will print all the properties
    timeline_fps = target_timeline.GetSetting('timelineFrameRate') # sync the fps so that the video lenght can be estimated correctly
    log_print(f'Timeline FPS: {timeline_fps}' )
    log_print(f'Insert {len(subClipList)} clips, {len(target_timeline.GetItemListInTrack("video", 1))} clips in timeline {target_timeline.GetName()}')
    resolve.OpenPage('Edit')
    
    # export subs
    if win.Find(expswitchID).Checked:
        subs = pysubs2.load(subtitle_path)
        subs_dst = osp.join(win.Find(targetID).Text, timeline_name + subtitle_type)
        compress_subtitles(subs, target_timeline.GetEndFrame()/timeline_fps, subs_dst)
    
    global_config['import_dir'] = win.Find(sourceID).Text
    global_config['export_dir'] = win.Find(targetID).Text 
    save_global_config(global_config)
    
    log_print('-' * 10 + 'Build Timeline Done' + '-' * 10)


def getTimelineName():
    t = datetime.now()
    i = 1
    
    # get names of all timelines
    timelines = getAllTimelines()
    
    # log_print(timelines)
    while True:
        s = f'{t.year:04d}{t.month:02d}{i:02d}'
        if s not in timelines:
            break
        i += 1
    return s

    
# Event handlers
def OnClose(ev):
    dispatcher.ExitLoop()
 
 
def OnRefresh(ev):
    files = glob(osp.join(win.Find(sourceID).Text, '*' + video_type))
    # file with srt:
    items = [f[:-4] for f in files if osp.exists(f[:-4] + subtitle_type)]
    items.sort(reverse=True)
    combo = win.Find(fileID)
    combo.Clear()
    combo.AddItems(items)
    # check timeline as well
    win.Find(timelineID).Text = getTimelineName()
    global_config['import_dir'] = win.Find(sourceID).Text
    global_config['export_dir'] = win.Find(targetID).Text 
    save_global_config(global_config)
    

# assign event handlers
win.On[winID].Close     = OnClose
win.On[execID].Clicked  = OnExec
win.On[refreshID].Clicked = OnRefresh
win.Find(sourceID).Text = global_config['import_dir']
win.Find(targetID).Text = global_config['export_dir']

OnRefresh(None)

# Main dispatcher loop
win.Show()
dispatcher.RunLoop()
