import json

config_filename = 'C:\\Users\\Public\\Documents\\davinci_plugin_save.json'

def load_global_config():
    try:
        global_config = json.load(open(config_filename, 'r'))
    except:
        global_config = {
            'export_dir': 'E:\\SynologyDrive\\PaperReview\\Final',
        }
    return global_config

global_config = load_global_config()
target_dir = global_config['export_dir']

if __name__ == '__main__':
    resolve = app.GetResolve()
    pm = resolve.GetProjectManager()
    pj = pm.GetCurrentProject()
    tl = pj.GetCurrentTimeline()
    # print(pj.GetRenderPresetList())
    pj.DeleteAllRenderJobs()
    timeline_name = pj.GetCurrentTimeline().GetName()

    pj.SetRenderSettings(
    {
        'TargetDir': target_dir,
        'CustomName': timeline_name
    }
    )
    pj.LoadRenderPreset('YouTube - 1080p')
    pj.AddRenderJob()
# pj.StartRendering()
