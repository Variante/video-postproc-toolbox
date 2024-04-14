import os.path as osp
from glob import glob

target_dir = 'E:\\SynologyDrive\\PaperReview\\Final'

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
