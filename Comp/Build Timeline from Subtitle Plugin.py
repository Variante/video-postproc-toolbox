import sys
import os.path as osp
from glob import glob
from datetime import datetime
import pysubs2

# some element IDs
winID = "com.blackmagicdesign.resolve.BuildTimelineScript"	# should be unique for single instancing
execID = "Exec"
refreshID = "Refresh"
sourceID = "SourcePath"
fileID = "File"
timelineID = "Timeline"
expswitchID = "ExportEnable"
expsubsID = "ExportSubs"
targetID = "TargetPath"


video_type = '.mkv'
subtitle_type = '.srt'

ui = fusion.UIManager
dispatcher = bmd.UIDispatcher(ui)

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
header = header + '<b>Build Timeline from Subtitle Script</b>'
header = header + '</h1></body></html>'

# define the window UI layout
win = dispatcher.AddWindow({
	'ID': winID,
	# 'Geometry': [ 100,100,600,300 ],
	'WindowTitle': "Build Timeline from Subtitle Script",
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
            ui.Label({'Text': 'Export path: ', 'Weight': 0}),
            ui.LineEdit({
                'ID': targetID,
                'Weight': 5
            })
        ]),
        ui.Button({ 'ID': execID,  'Text': "Import Videos and Export Subtitles" })
        
	])
)

# Event handlers
def OnClose(ev):
	dispatcher.ExitLoop()
    
    
def getAllTimelines():
    resolve = app.GetResolve()
    projectManager = resolve.GetProjectManager()
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
            subs[i].text += "\\n" + subs[i+1].text  # Merge text of two subtitles
            del subs[i+1]
        else:
            i += 1
    return subs


def compress_subtitles(subs, output_subtitle_path):
    i = 0
    if len(subs) == 0:
        return
    
    while i < len(subs):
        # Adjust the start of the next subtitle to immediately follow the current one
        l = subs[i].end - subs[i].start
        if i == 0:
            subs[i].start = 0
        else:
            subs[i].start = subs[i - 1].end + 1
        subs[i].end = subs[i].start + l
        i += 1
        
    # Save the adjusted subtitles
    subs.save(output_subtitle_path)


def OnExec(ev):
	# import file
    if win.Find(fileID).Count == 0:
        print('Please select a file to import')
        return
    
    # add video file to media pool
    resolve = app.GetResolve()
    ms = resolve.GetMediaStorage()
    file_base = win.Find(fileID).CurrentText
    ms.AddItemListToMediaPool(file_base + video_type)

    # get names ready
    _, file_name = osp.split(file_base)
    full_file_name = file_name + video_type
    timeline_name = win.Find(timelineID).Text
    # print(f'{full_file_name = } {timeline_name = }')

    # find the clip items (media pool item)
    projectManager = resolve.GetProjectManager()
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
    fps = clip.GetClipProperty('FPS')
    
    subClipList = []
    
    for i, sub in enumerate(merge_close_subtitles(subs)):
        start = sub.start / 1000.0  # Convert milliseconds to seconds
        end = sub.end / 1000.0
        subClipList.append({
            "mediaPoolItem": clip,
            "startFrame": int(start * fps),
            "endFrame": int(end * fps),
        })
    if len(subClipList) == 0:
        print('No clip founded, exit')
        return
    # find the timeline to insert
    timelines = getAllTimelines()
    if timeline_name in timelines:
        target_timeline = timelines[timeline_name]
        project.SetCurrentTimeline(target_timeline)
        mediaPool.AppendToTimeline(subClipList)
    else:
        target_timeline = mediaPool.CreateTimelineFromClips(timeline_name, subClipList[:1])
        project.SetCurrentTimeline(target_timeline)
        mediaPool.AppendToTimeline(subClipList[1:])
    print(f'Insert {len(subClipList)} clips, {len(target_timeline.GetItemListInTrack("video", 1))} clips in timeline {target_timeline.GetName()}')
    resolve.OpenPage('Edit')
    
    # export subs
    if win.Find(expswitchID).Checked:
        subs = pysubs2.load(subtitle_path)
        subs_dst = osp.join(win.Find(targetID).Text, target_timeline.GetName() + subtitle_type)
        compress_subtitles(subs, subs_dst)
    
    
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
    


# assign event handlers
win.On[winID].Close     = OnClose
win.On[execID].Clicked  = OnExec
win.On[refreshID].Clicked = OnRefresh

def getTimelineName():
    t = datetime.now()
    i = 1
    
    resolve = app.GetResolve()
    projectManager = resolve.GetProjectManager()
    project = projectManager.GetCurrentProject()
    
    # get names of all timelines
    timelines = getAllTimelines()
    
    # print(timelines)
    while True:
        s = f'{t.year:04d}{t.month:02d}{i:02d}'
        if s not in timelines:
            break
        i += 1
    return s
    


win.Find(sourceID).Text = 'D:\\Video2024'
try:
    from export_to_final import target_dir
    win.Find(targetID).Text = target_dir
except:
    pass
OnRefresh(None)

# Main dispatcher loop
win.Show()
dispatcher.RunLoop()

