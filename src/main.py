import err_processer as _
import init_logging as _
import fix_workpath as _
import import_argvs as _
import check_edgechromium as _
import check_bin as _

import json
import sys
import time
import logging
import typing
import platform
from threading import Thread
from os import popen
from os.path import exists
from ntpath import basename

import requests
from PIL import Image, ImageFilter
from pydub import AudioSegment

import webcv
import dxsound
import chartobj_phi
import chartobj_rpe
import chartfuncs_phi
import chartfuncs_rpe
import const
import tool_funcs
import dialog
import info_loader
import ppr_help
import file_loader
import phira_resource_pack
import phicore
import tempdir
import socket_webviewbridge
import wcv2matlike
import needrelease
from dxsmixer import mixer
from exitfunc import exitfunc
from graplib_webview import *

import load_extended as _

if len(sys.argv) == 1:
    print(ppr_help.HELP_ZH)
    raise SystemExit

tempdir.clearTempDir()
temp_dir = tempdir.createTempDir()

enable_clicksound = "--noclicksound" not in sys.argv
debug = "--debug" in sys.argv
debug_noshow_transparent_judgeline = "--debug-noshow-transparent-judgeline" in sys.argv
loop = "--loop" in sys.argv
lfdaot = "--lfdaot" in sys.argv
lfdoat_file = "--lfdaot-file" in sys.argv
render_range_more = "--render-range-more" in sys.argv


render_range_more_scale = 2.0 if "--render-range-more-scale" not in sys.argv else eval(sys.argv[sys.argv.index("--render-range-more-scale") + 1])
noautoplay = "--noautoplay" in sys.argv
rtacc = "--rtacc" in sys.argv
lowquality = "--lowquality" in sys.argv
lowquality_scale = float(sys.argv[sys.argv.index("--lowquality-scale") + 1]) ** 0.5 if "--lowquality-scale" in sys.argv else 2.0 ** 0.5
showfps = "--showfps" in sys.argv
lfdaot_start_frame_num = int(eval(sys.argv[sys.argv.index("--lfdaot-start-frame-num") + 1])) if "--lfdaot-start-frame-num" in sys.argv else 0
lfdaot_run_frame_num = int(eval(sys.argv[sys.argv.index("--lfdaot-run-frame-num") + 1])) if "--lfdaot-run-frame-num" in sys.argv else float("inf")
speed = float(sys.argv[sys.argv.index("--speed") + 1]) if "--speed" in sys.argv else 1.0
clickeffect_randomblock_roundn = eval(sys.argv[sys.argv.index("--clickeffect-randomblock-roundn") + 1]) if "--clickeffect-randomblock-roundn" in sys.argv else 0.0
noplaychart = "--noplaychart" in sys.argv
clicksound_volume = float(sys.argv[sys.argv.index("--clicksound-volume") + 1]) if "--clicksound-volume" in sys.argv else 1.0
musicsound_volume = float(sys.argv[sys.argv.index("--musicsound-volume") + 1]) if "--musicsound-volume" in sys.argv else 1.0
lowquality_imjscvscale_x = float(sys.argv[sys.argv.index("--lowquality-imjscvscale-x") + 1]) if "--lowquality-imjscvscale-x" in sys.argv else 1.0
lowquality_imjs_maxsize = float(sys.argv[sys.argv.index("--lowquality-imjs-maxsize") + 1]) if "--lowquality-imjs-maxsize" in sys.argv else 256
enable_controls = "--enable-controls" in sys.argv
wl_more_chinese = "--wl-more-chinese" in sys.argv
skip_time = float(sys.argv[sys.argv.index("--skip-time") + 1]) if "--skip-time" in sys.argv else 0.0
enable_jscanvas_bitmap = "--enable-jscanvas-bitmap" in sys.argv
respath = sys.argv[sys.argv.index("--res") + 1] if "--res" in sys.argv else "./resources/resource_packs/default"
usu169 = "--usu169" in sys.argv
render_video = "--render-video" in sys.argv
render_video_fps = float(sys.argv[sys.argv.index("--render-video-fps") + 1]) if "--render-video-fps" in sys.argv else 60.0
render_video_fourcc = sys.argv[sys.argv.index("--render-video-fourcc") + 1] if "--render-video-fourcc" in sys.argv else "mp4v"

if lfdaot and noautoplay:
    noautoplay = False
    logging.warning("if use --lfdaot, you cannot use --noautoplay")

if lfdaot and speed != 1.0:
    speed = 1.0
    logging.warning("if use --lfdaot, you cannot use --speed")

if lfdaot and skip_time != 0.0:
    skip_time = 0.0
    logging.warning("if use --lfdaot, you cannot use --skip-time")

if render_video and noautoplay:
    noautoplay = False
    logging.warning("if use --render-video, you cannot use --noautoplay")

if render_video and showfps:
    showfps = False
    logging.warning("if use --render-video, you cannot use --showfps")
    
if "--clickeffect-easing" in sys.argv:
    phicore.clickEffectEasingType = int(sys.argv[sys.argv.index("--clickeffect-easing") + 1])

combotips = ("AUTOPLAY" if not noautoplay else "COMBO") if "--combotips" not in sys.argv else sys.argv[sys.argv.index("--combotips") + 1]
mixer.init()

if "--phira-chart" in sys.argv:
    logging.info("Downloading phira chart...")
    pctid = sys.argv[sys.argv.index("--phira-chart") + 1]
    apiresult = requests.get(f"https://phira.5wyxi.com/chart/{pctid}").json()
    if "error" in apiresult:
        logging.error(f"phira api: {apiresult["error"]}")
        raise SystemExit
    
    sys.argv.insert(1, f"{temp_dir}/phira-temp-chart.zip" if "--phira-chart-save" not in sys.argv else sys.argv[sys.argv.index("--phira-chart-save") + 1])
    with open(sys.argv[1], "wb") as f:
        with requests.get(apiresult["file"], stream=True) as reqs:
            for content in reqs.iter_content(chunk_size=1024):
                f.write(content)
    logging.info("Downloaded phira chart.")

logging.info("Unpack Chart...")
popen(f"7z x \"{sys.argv[1]}\" -o\"{temp_dir}\" -y").read()

logging.info("Loading All Files of Chart...")
files_dict = {
    "charts": [],
    "images": [],
    "audio": [],
}
chartimages = {}
cfrfp_procer: typing.Callable[[str], str] = lambda x: x.replace(f"{temp_dir}/", "")

for item in tool_funcs.getAllFiles(temp_dir):
    if item.endswith("info.txt") or item.endswith("info.csv") or item.endswith("info.yml") or item.endswith("extra.json") or item.endswith(".glsl"):
        continue
    
    item_rawname = cfrfp_procer(item)
    loadres = file_loader.loadfile(item)
    
    match loadres.filetype:
        case file_loader.FILE_TYPE.CHART:
            files_dict["charts"].append([item, loadres.data])
            
        case file_loader.FILE_TYPE.IMAGE:
            files_dict["images"].append([item, loadres.data])
            
        case file_loader.FILE_TYPE.SONG:
            files_dict["audio"].append(item)
        
        case file_loader.FILE_TYPE.UNKNOW:
            logging.warning(f"Unknow resource type. path = {item_rawname}") # errors: ")
            # for e in loadres.errs: logging.warning(f"\t{repr(e)}")
                    
if not files_dict["charts"]:
    logging.fatal("No Chart File Found")
    raise SystemExit

if not files_dict["audio"]:
    logging.fatal("No Audio File Found")
    raise SystemExit

if not files_dict["images"]:
    logging.warning("No Image File Found")
    files_dict["images"].append(["default", Image.new("RGB", (16, 9), "black")])

chart_fp: str
chart_json: dict
cimg_fp: str
chart_image: Image.Image
audio_fp: str

chart_index = file_loader.choosefile(
    fns = map(lambda x: x[0], files_dict["charts"]),
    prompt = "请选择谱面文件: ", rawprocer = cfrfp_procer
)
chart_fp, chart_json = files_dict["charts"][chart_index]

if "formatVersion" in chart_json:
    CHART_TYPE = const.CHART_TYPE.PHI
elif "META" in chart_json:
    CHART_TYPE = const.CHART_TYPE.RPE
else:
    logging.fatal("This is what format chart ???")
    raise SystemExit

if exists(f"{temp_dir}/extra.json"):
    try:
        logging.info("found extra.json, loading...")
        extra = chartfuncs_rpe.loadExtra(json.load(open(f"{temp_dir}/extra.json", "r", encoding="utf-8")))
        logging.info("loading extra.json successfully")
    except SystemExit as e:
        logging.error("loading extra.json failed")
        
if "extra" not in globals():
    extra = chartfuncs_rpe.loadExtra({})
    
def loadChartObject(first: bool = False):
    global chart_obj
    
    if CHART_TYPE == const.CHART_TYPE.PHI:
        chart_obj = chartfuncs_phi.loadChartObject(chart_json)
    elif CHART_TYPE == const.CHART_TYPE.RPE:
        chart_obj = chartfuncs_rpe.loadChartObject(chart_json)
        
        chart_obj.META.RPEVersion = (
            sys.argv[sys.argv.index("--rpeversion") + 1]
            if "--rpeversion" in sys.argv
            else chart_obj.META.RPEVersion
        )
        chart_obj.extra = extra
    
    if not first:
        updateCoreConfig()
        
loadChartObject(True)

cimg_index = file_loader.choosefile(
    fns = map(lambda x: x[0], files_dict["images"]),
    prompt = "请选择背景图片: ", rawprocer = cfrfp_procer,
    default = chart_obj.META.background if CHART_TYPE == const.CHART_TYPE.RPE else None
)
cimg_fp, chart_image = files_dict["images"][cimg_index]
chart_image = chart_image.convert("RGB")

audio_index = file_loader.choosefile(
    fns = files_dict["audio"],
    prompt = "请选择音频文件: ", rawprocer = cfrfp_procer,
    default = chart_obj.META.song if CHART_TYPE == const.CHART_TYPE.RPE else None
)
audio_fp = files_dict["audio"][audio_index]

raw_audio_fp = audio_fp
if speed != 1.0:
    logging.info(f"Processing audio, rate = {speed}")
    seg: AudioSegment = AudioSegment.from_file(audio_fp)
    seg = seg._spawn(seg.raw_data, overrides = {
        "frame_rate": int(seg.frame_rate * speed)
    }).set_frame_rate(seg.frame_rate)
    audio_fp = f"{temp_dir}/ppr_temp_audio_{time.time()}.wav"
    seg.export(audio_fp, format="wav")

mixer.music.load(audio_fp)
raw_audio_length = mixer.music.get_length()
audio_length = raw_audio_length + (chart_obj.META.offset / 1000 if CHART_TYPE == const.CHART_TYPE.RPE else chart_obj.offset)
all_inforamtion = {}
logging.info("Loading Chart Information...")

ChartInfoLoader = info_loader.InfoLoader([f"{temp_dir}/info.csv", f"{temp_dir}/info.txt", f"{temp_dir}/info.yml"])
chart_information = ChartInfoLoader.get(basename(chart_fp), basename(raw_audio_fp), basename(cimg_fp))

if CHART_TYPE == const.CHART_TYPE.RPE and chart_information is ChartInfoLoader.default_info:
    chart_information["Name"] = chart_obj.META.name
    chart_information["Artist"] = chart_obj.META.composer
    chart_information["Level"] = chart_obj.META.level
    chart_information["Charter"] = chart_obj.META.charter

logging.info("Loading Chart Information Successfully")
logging.info("Chart Info: ")
for k,v in chart_information.items():
    logging.info(f"           {k}: {v}")

def loadResource():
    global globalNoteWidth
    global note_max_width, note_max_height
    global note_max_size_half
    global animation_image
    global WaitLoading, LoadSuccess
    global chart_res
    global cksmanager
    
    logging.info("Loading Resource...")
    WaitLoading = mixer.Sound("./resources/WaitLoading.mp3")
    LoadSuccess = mixer.Sound("./resources/LoadSuccess.wav")
    Thread(target=WaitLoading_FadeIn, daemon = True).start()
    LoadSuccess.set_volume(0.75)
    WaitLoading.play(-1)
    noteWidth_raw = (0.125 * w + 0.2 * h) / 2
    globalNoteWidth = noteWidth_raw * (eval(sys.argv[sys.argv.index("--scale-note") + 1]) if "--scale-note" in sys.argv else 1.0)
    
    phi_rpack = phira_resource_pack.PhiraResourcePack(respath)
    phi_rpack.setToGlobal()
    phi_rpack.printInfo()
    
    Resource = {
        "levels":{
            "AP": Image.open("./resources/levels/AP.png"),
            "FC": Image.open("./resources/levels/FC.png"),
            "V": Image.open("./resources/levels/V.png"),
            "S": Image.open("./resources/levels/S.png"),
            "A": Image.open("./resources/levels/A.png"),
            "B": Image.open("./resources/levels/B.png"),
            "C": Image.open("./resources/levels/C.png"),
            "F": Image.open("./resources/levels/F.png")
        },
        "le_warn": Image.open("./resources/le_warn.png"),
        "Retry": Image.open("./resources/Retry.png"),
        "Arrow_Right": Image.open("./resources/Arrow_Right.png"),
        "Over": mixer.Sound("./resources/Over.mp3"),
        "Pause": mixer.Sound("./resources/Pause.wav"),
        "PauseImg": Image.open("./resources/Pause.png"),
        "ButtonLeftBlack": Image.open("./resources/Button_Left_Black.png"),
        "ButtonRightBlack": None
    }
    
    Resource.update(phi_rpack.createResourceDict())
    
    respacker = webcv.PILResourcePacker(root)
    
    background_image_blur = chart_image.filter(ImageFilter.GaussianBlur(sum(chart_image.size) / 50))
    respacker.reg_img(background_image_blur, "background_blur")
    
    animation_image = chart_image.convert("RGBA")
    tool_funcs.cutAnimationIllImage(animation_image)
    
    chart_image_gradientblack = animation_image.copy()
    chart_image_gradient = tool_funcs.createDownBlockImageGrd().resize(chart_image_gradientblack.size)
    chart_image_gradientblack.paste(chart_image_gradient, (0, 0), chart_image_gradient)
    
    Resource["ButtonRightBlack"] = Resource["ButtonLeftBlack"].transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)
    const.set_NOTE_DUB_FIXSCALE(Resource["Notes"]["Hold_Body_dub"].width / Resource["Notes"]["Hold_Body"].width)
    
    for k, v in Resource["Notes"].items():
        respacker.reg_img(Resource["Notes"][k], f"Note_{k}")
    
    for i in range(phira_resource_pack.globalPack.effectFrameCount): # reg click effect
        respacker.reg_img(Resource["Note_Click_Effect"]["Perfect"][i], f"Note_Click_Effect_Perfect_{i + 1}")
        respacker.reg_img(Resource["Note_Click_Effect"]["Good"][i], f"Note_Click_Effect_Good_{i + 1}")
        
    for k,v in Resource["levels"].items(): # reg levels img
        respacker.reg_img(v, f"Level_{k}")
        
    respacker.reg_img(Resource["le_warn"], "le_warn")
    respacker.reg_img(chart_image, "chart_image")
    respacker.reg_img(chart_image_gradientblack, "chart_image_gradientblack")
    respacker.reg_img(Resource["Retry"], "Retry")
    respacker.reg_img(Resource["Arrow_Right"], "Arrow_Right")
    respacker.reg_img(Resource["PauseImg"], "PauseImg")
    respacker.reg_img(Resource["ButtonLeftBlack"], "ButtonLeftBlack")
    respacker.reg_img(Resource["ButtonRightBlack"], "ButtonRightBlack")
    
    chart_res = {}
    
    if CHART_TYPE == const.CHART_TYPE.RPE:
        imfns: list[str] = list(map(lambda x: x[0], files_dict["images"]))
        imobjs: list[Image.Image] = list(map(lambda x: x[1], files_dict["images"]))
        
        for line in chart_obj.judgeLineList:
            if line.Texture == "line.png": continue
            if not line.isGif:
                paths = [ # fuck charters
                    f"{temp_dir}/{line.Texture}",
                    f"{temp_dir}/{line.Texture}.png",
                    f"{temp_dir}/{line.Texture}.jpg",
                    f"{temp_dir}/{line.Texture}.jpeg"
                ]
                
                for p in paths:
                    if tool_funcs.fileinlist(p, imfns):
                        texture_index = tool_funcs.findfileinlist(p, imfns)
                        texture: Image.Image = imobjs[texture_index]
                        chart_res[line.Texture] = (texture.convert("RGBA"), texture.size)
                        logging.info(f"Loaded line texture {line.Texture}")
                        break
                else:
                    logging.warning(f"Cannot find texture {line.Texture}")
                    texture = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
                    chart_res[line.Texture] = (texture, texture.size)
                    
                respacker.reg_img(chart_res[line.Texture][0], f"lineTexture_{chart_obj.judgeLineList.index(line)}")
            else:
                mp4data, size = tool_funcs.gif2mp4(f"{temp_dir}/{line.Texture}")
                chart_res[line.Texture] = (None, size)
                name = f"lineTexture_{chart_obj.judgeLineList.index(line)}"
                root.reg_res(mp4data, f"{name}.mp4")
                root.wait_jspromise(f"loadvideo(\"{root.get_resource_path(f"{name}.mp4")}\", '{name}_img');")
    
    root.reg_res(open("./resources/font.ttf", "rb").read(), "pgrFont.ttf")
    root.reg_res(open("./resources/font-thin.ttf", "rb").read(), "pgrFontThin.ttf")
    respacker.load(*respacker.pack())
    
    root.wait_jspromise(f"loadFont('pgrFont', \"{root.get_resource_path("pgrFont.ttf")}\");")
    root.wait_jspromise(f"loadFont('pgrFontThin', \"{root.get_resource_path("pgrFontThin.ttf")}\");")
    root.unreg_res("pgrFont.ttf")
    root.unreg_res("pgrFontThin.ttf")
    
    # root.file_server.shutdown()
    note_max_width = globalNoteWidth * const.NOTE_DUB_FIXSCALE
    note_max_height = max((
        note_max_width / Resource["Notes"]["Tap"].width * Resource["Notes"]["Tap"].height,
        note_max_width / Resource["Notes"]["Tap_dub"].width * Resource["Notes"]["Tap_dub"].height,
        note_max_width / Resource["Notes"]["Drag"].width * Resource["Notes"]["Drag"].height,
        note_max_width / Resource["Notes"]["Drag_dub"].width * Resource["Notes"]["Drag_dub"].height,
        note_max_width / Resource["Notes"]["Flick"].width * Resource["Notes"]["Flick"].height,
        note_max_width / Resource["Notes"]["Flick_dub"].width * Resource["Notes"]["Flick_dub"].height,
        note_max_width / Resource["Notes"]["Hold_Head"].width * Resource["Notes"]["Hold_Head"].height,
        note_max_width / Resource["Notes"]["Hold_Head_dub"].width * Resource["Notes"]["Hold_Head_dub"].height,
        note_max_width / Resource["Notes"]["Hold_End"].width * Resource["Notes"]["Hold_End"].height
    ))
    note_max_size_half = ((note_max_width ** 2 + note_max_height ** 2) ** 0.5) / 2
                
    shaders = {
        "chromatic": open("./shaders/chromatic.glsl", "r", encoding="utf-8").read(),
        "circleBlur": open("./shaders/circle_blur.glsl", "r", encoding="utf-8").read(),
        "fisheye": open("./shaders/fisheye.glsl", "r", encoding="utf-8").read(),
        "glitch": open("./shaders/glitch.glsl", "r", encoding="utf-8").read(),
        "grayscale": open("./shaders/grayscale.glsl", "r", encoding="utf-8").read(),
        "noise": open("./shaders/noise.glsl", "r", encoding="utf-8").read(),
        "pixel": open("./shaders/pixel.glsl", "r", encoding="utf-8").read(),
        "radialBlur": open("./shaders/radial_blur.glsl", "r", encoding="utf-8").read(),
        "shockwave": open("./shaders/shockwave.glsl", "r", encoding="utf-8").read(),
        "vignette": open("./shaders/vignette.glsl", "r", encoding="utf-8").read()
    }
    
    if CHART_TYPE == const.CHART_TYPE.RPE:
        for line in chart_obj.judgeLineList:
            for note in line.notes:
                if note.hitsound_reskey not in Resource["Note_Click_Audio"]:
                    try:
                        Resource["Note_Click_Audio"][note.hitsound_reskey] = dxsound.directSound(f"{temp_dir}/{note.hitsound}")
                        logging.info(f"Loaded note hitsound {note.hitsound}")
                    except Exception as e:
                        logging.warning(f"Cannot load note hitsound {note.hitsound} for note due to {e}")
        
        if chart_obj.extra is not None:
            for effect in chart_obj.extra.effects:
                if effect.shader not in shaders.keys():
                    try:
                        shaders[effect.shader] = tool_funcs.fixShader(open(f"{temp_dir}/{effect.shader}", "r", encoding="utf-8").read())
                        const.EXTRA_DEFAULTS[effect.shader] = tool_funcs.getShaderDefault(shaders[effect.shader])
                    except Exception as e:
                        logging.warning(f"Cannot load shader {effect.shader} due to {e}")
            
            shadernames = list(set(effect.shader for effect in chart_obj.extra.effects))

            for name, glsl in shaders.items():
                if name not in shadernames: continue
                root.run_js_code(f"mainShaderLoader.load({repr(name)}, {repr(glsl)});")
                if (glerr := root.run_js_code("GLERR;")) is not None:
                    logging.warning(f"Cannot compile shader {name} due to {glerr}")
                else:
                    logging.info(f"Loaded shader {name}")
    
    cksmanager = phicore.ClickSoundManager(Resource["Note_Click_Audio"])
    logging.info("Load Resource Successfully")
    return Resource

def WaitLoading_FadeIn():
    for i in range(100):
        WaitLoading.set_volume((i + 1) / 100)
        time.sleep(2 / 100)

def showStart():
    WaitLoading.fadeout(450)
    
    def dle_warn(a: float):
        drawAlphaImage("le_warn", 0, 0, w, h, a, wait_execute=True)
    
    animationst = time.time()
    while time.time() - animationst < 1.0:
        clearCanvas(wait_execute=True)
        p = (time.time() - animationst) / 1.0
        dle_warn(1.0 - (1.0 - tool_funcs.fixorp(p)) ** 4)
        root.run_js_wait_code()
    
    time.sleep(0.35)
    
    animationst = time.time()
    while time.time() - animationst < 1.0:
        clearCanvas(wait_execute=True)
        phicore.drawBg()
        p = (time.time() - animationst) / 1.0
        dle_warn((tool_funcs.fixorp(p) - 1.0) ** 4)
        root.run_js_wait_code()
    
    time.sleep(0.25)
    clearCanvas(wait_execute=True)
    phicore.drawBg()
    root.run_js_wait_code()
    Thread(target=playerStart, daemon=True).start()

def checkOffset(now_t: float):
    global show_start_time
    
    dt = tool_funcs.checkOffset(now_t, raw_audio_length, mixer)
    if dt != 0.0:
        show_start_time += dt
        updateCoreConfig()

def getLfdaotFuncs():
    _getfuncs = lambda obj: {fn: getattr(obj, fn) for fn in dir(obj) if not fn.startswith("_")}
    maps = [
        _getfuncs(root),
        _getfuncs(phicore)
    ]
    result = {k: v for i in maps for k, v in i.items()}
    
    if len(result) != sum(len(i) for i in maps):
        assert False, "Duplicate function name detected"
        
    return result

def playerStart():
    global show_start_time, cksmanager
    
    Resource["Over"].stop()
    
    phicore.loadingAnimation()
    phicore.lineOpenAnimation()

    show_start_time = time.time() - skip_time
    PhiCoreConfigObject.show_start_time = show_start_time
    updateCoreConfig()
    now_t = 0
    
    if not (lfdaot or render_video):
        mixer.music.play()
        mixer.music.set_pos(skip_time)
        while not mixer.music.get_busy(): pass
        if noautoplay:
            if CHART_TYPE == const.CHART_TYPE.PHI:
                pplm_proxy = chartobj_phi.PPLMPHI_Proxy(chart_obj)
            elif CHART_TYPE == const.CHART_TYPE.RPE:
                pplm_proxy = chartobj_rpe.PPLMRPE_Proxy(chart_obj)
            
            pppsm = tool_funcs.PhigrosPlayManager(chart_obj.note_num)
            pplm = tool_funcs.PhigrosPlayLogicManager(
                pplm_proxy, pppsm,
                enable_clicksound, lambda nt: Resource["Note_Click_Audio"][nt].play()
            )
            
            convertTime2Chart = lambda t: (t - show_start_time) * speed - (0.0 if CHART_TYPE == const.CHART_TYPE.PHI else chart_obj.META.offset / 1000)
            root.jsapi.set_attr("PhigrosPlay_KeyDown", lambda t, key: pplm.pc_click(convertTime2Chart(t if not webcv.disengage_webview else (now_t + show_start_time)), key))
            root.jsapi.set_attr("PhigrosPlay_KeyUp", lambda t, key: pplm.pc_release(convertTime2Chart(t if not webcv.disengage_webview else (now_t + show_start_time)), key))
            root.jsapi.set_attr("PhigrosPlay_TouchStart", lambda t, x, y, i: pplm.mob_touchstart(convertTime2Chart(t), x / w, y / h, i))
            root.jsapi.set_attr("PhigrosPlay_TouchMove", lambda t, x, y, i: pplm.mob_touchmove(convertTime2Chart(t), x / w, y / h, i))
            root.jsapi.set_attr("PhigrosPlay_TouchEnd", lambda i: pplm.mob_touchend(i))
            pplm.bind_events(root)
            
        play_restart_flag = False
        pause_flag = False
        pause_st = float("nan")
        
        def _f(): nonlocal play_restart_flag; play_restart_flag = True
        
        @tool_funcs.runByThread
        def space():
            global show_start_time
            nonlocal pause_flag, pause_st
            
            if not pause_flag:
                pause_flag = True
                mixer.music.pause()
                Resource["Pause"].play()
                pause_st = time.time()
            else:
                mixer.music.unpause()
                show_start_time += time.time() - pause_st
                pause_flag = False
        
        @tool_funcs.runByThread
        def dumpChart():
            if noautoplay: return
            
            fn = dialog.savefile(fn="dump.json")
            if fn is None: return
            
            with open(fn, "w", encoding="utf-8") as f:
                f.write(json.dumps(chart_obj.dump(), ensure_ascii=False))
                
        root.jsapi.set_attr("Noautoplay_Restart", _f)
        root.jsapi.set_attr("SpaceClicked", space)
        root.jsapi.set_attr("DumpChart", dumpChart)
        root.run_js_code("_Noautoplay_Restart = (e) => {if (e.altKey && e.ctrlKey && e.repeat && e.key.toLowerCase() == 'r') pywebview.api.call_attr('Noautoplay_Restart');};") # && e.repeat 为了判定长按
        root.run_js_code("_SpaceClicked = (e) => {if (e.key == ' ' && !e.repeat) pywebview.api.call_attr('SpaceClicked');};")
        root.run_js_code("_DumpChart = (e) => {if (e.altKey && e.ctrlKey && e.repeat && e.key.toLowerCase() == 'd') pywebview.api.call_attr('DumpChart');};")
        root.run_js_code("window.addEventListener('keydown', _Noautoplay_Restart);")
        root.run_js_code("window.addEventListener('keydown', _SpaceClicked);")
        root.run_js_code("window.addEventListener('keydown', _DumpChart);")
        
        while True:
            while pause_flag: time.sleep(1 / 30)
            
            now_t = time.time() - show_start_time
            checkOffset(now_t - skip_time)
            if CHART_TYPE == const.CHART_TYPE.PHI:
                Task = phicore.GetFrameRenderTask_Phi(now_t, pplm = pplm if noautoplay else None)
            elif CHART_TYPE == const.CHART_TYPE.RPE:
                Task = phicore.GetFrameRenderTask_Rpe(now_t, pplm = pplm if noautoplay else None)
                
            Task.ExecTask()
            
            break_flag = phicore.processExTask(Task.ExTask)
            
            if break_flag:
                break
            
            if play_restart_flag:
                break
        
        if noautoplay:
            pplm.unbind_events(root)
        
        root.run_js_code("window.removeEventListener('keydown', _Noautoplay_Restart);")
        root.run_js_code("window.removeEventListener('keydown', _SpaceClicked);")
        
        if play_restart_flag:
            mixer.music.fadeout(250)
            loadChartObject()
            Thread(target=playerStart, daemon=True).start()
            return
        
    elif lfdaot:
        lfdaot_tasks: dict[int, chartobj_phi.FrameRenderTask] = {}
        frame_speed = 60
        if "--lfdaot-frame-speed" in sys.argv:
            frame_speed = eval(sys.argv[sys.argv.index("--lfdaot-frame-speed") + 1])
        frame_count = lfdaot_start_frame_num
        frame_time = 1 / frame_speed
        allframe_num = int(audio_length / frame_time) + 1
        
        if lfdaot and not lfdoat_file: # eq if not lfdoat_file
            while True:
                if frame_count * frame_time > audio_length or frame_count - lfdaot_start_frame_num >= lfdaot_run_frame_num:
                    break
                
                now_t = frame_count * frame_time
                
                if CHART_TYPE == const.CHART_TYPE.PHI:
                    lfdaot_tasks.update({frame_count: phicore.GetFrameRenderTask_Phi(now_t, None)})
                elif CHART_TYPE == const.CHART_TYPE.RPE:
                    lfdaot_tasks.update({frame_count: phicore.GetFrameRenderTask_Rpe(now_t, None)})
                
                frame_count += 1
                
                print(f"\rLoadFrameData: {frame_count} / {allframe_num}", end="")
            
            if "--lfdaot-file-savefp" in sys.argv:
                lfdaot_fp = sys.argv[sys.argv.index("--lfdaot-file-savefp") + 1]
            else:
                lfdaot_fp = dialog.savefile(fn="Chart.lfdaot")
            
            if lfdaot_fp is not None:
                recorder = chartobj_phi.FrameTaskRecorder(
                    meta = chartobj_phi.FrameTaskRecorder_Meta(
                        frame_speed = frame_speed,
                        frame_num = len(lfdaot_tasks),
                        size = (w, h)
                    ),
                    data = lfdaot_tasks.values()
                )
                
                with open(lfdaot_fp, "w", encoding="utf-8") as f:
                    recorder.stringify(f)
                    
            if "--lfdaot-file-output-autoexit" in sys.argv:
                root.destroy()
                return
            
        else: #--lfdaot-file
            fp = sys.argv[sys.argv.index("--lfdaot-file") + 1]
            with open(fp,"r",encoding="utf-8") as f:
                data = json.load(f)
            frame_speed = data["meta"]["frame_speed"]
            frame_time = 1 / frame_speed
            allframe_num = data["meta"]["frame_num"]
            
            funcmap = getLfdaotFuncs()
            
            for index,Task_data in enumerate(data["data"]):
                lfdaot_tasks.update({
                    index: chartobj_phi.FrameRenderTask(
                        RenderTasks = [
                            chartobj_phi.RenderTask(
                                func = funcmap[render_task_data["func_name"]],
                                args = tuple(render_task_data["args"]),
                                kwargs = render_task_data["kwargs"]
                            )
                            for render_task_data in Task_data["render"]
                        ],
                        ExTask = tuple(Task_data["ex"])
                    )
                })
            if data["meta"]["size"] != [w, h]:
                logging.warning("The size of the lfdaot file is not the same as the size of the window")
        
        mixer.music.play()
        while not mixer.music.get_busy(): pass
        
        totm: tool_funcs.TimeoutTaskManager[chartobj_phi.FrameRenderTask] = tool_funcs.TimeoutTaskManager()
        totm.valid = lambda x: bool(x)
        
        for fc, task in lfdaot_tasks.items():
            totm.add_task(fc, task.ExTask)
        
        pst = time.time()
        
        while True:
            now_t = time.time() - pst
            music_play_fcount = int(now_t / frame_time)
            
            try:
                Task: chartobj_phi.FrameRenderTask = lfdaot_tasks[music_play_fcount]
            except KeyError:
                continue
            
            Task.ExecTask(clear=False)
            extasks = totm.get_task(music_play_fcount)
            
            break_flag_oside = False
            
            for extask in extasks:
                break_flag = phicore.processExTask(extask)
                
                if break_flag:
                    break_flag_oside = True
                    break
            
            if break_flag_oside:
                break
            
            pst += tool_funcs.checkOffset(now_t, raw_audio_length, mixer)
    elif render_video:
        video_fp = sys.argv[sys.argv.index("--render-video-savefp") + 1] if "--render-video-savefp" in sys.argv else dialog.savefile(fn="render_video.mp4")
        
        if video_fp is None:
            root.destroy()
            return
        
        import cv2
        writer = cv2.VideoWriter(
            video_fp,
            cv2.VideoWriter.fourcc(*render_video_fourcc),
            render_video_fps,
            (w, h),
            True
        )
        needrelease.add(writer.release)
        
        def writeFrame(data: bytes):
            matlike = tool_funcs.bytes2matlike(data, w, h)
            writer.write(matlike)
        
        wcv2matlike.callback = writeFrame
        httpd, port = wcv2matlike.createServer()
        
        now_t = 0.0
        while now_t < audio_length:
            if CHART_TYPE == const.CHART_TYPE.PHI:
                Task = phicore.GetFrameRenderTask_Phi(now_t, None)
            elif CHART_TYPE == const.CHART_TYPE.RPE:
                Task = phicore.GetFrameRenderTask_Rpe(now_t, None)
                
            Task.ExecTask()
            root.wait_jspromise(f"uploadFrame('http://127.0.0.1:{port}/');")
            now_t += 1 / render_video_fps
        
        httpd.shutdown()
        writer.release()
        needrelease.remove(writer.release)
                
        if "--render-video-autoexit" in sys.argv:
            root.destroy()
            return
        
    else:
        assert False, "never"
    
    mixer.music.set_volume(1.0)
    phicore.initSettlementAnimation(pplm if noautoplay else None)
    
    def Chart_Finish_Animation():
        animation_1_time = 0.75
        a1_combo = pplm.ppps.getCombo() if noautoplay else None
        
        animation_1_start_time = time.time()
        while True:
            p = (time.time() - animation_1_start_time) / animation_1_time
            if p > 1.0: break
            phicore.lineCloseAimationFrame(p, a1_combo)
        
        time.sleep(0.25)
        Resource["Over"].play(-1)
    
        animation_2_time = 3.5
        animation_2_start_time = time.time()
        a2_loop_clicked = False
        a2_continue_clicked = False
        a2_break = False
        
        def whileCheck():
            nonlocal a2_break
            while True:
                if a2_loop_clicked or (loop and (time.time() - animation_2_start_time) > 0.25):
                    def _f():
                        loadChartObject()
                        playerStart()
                    Thread(target=_f, daemon=True).start()
                    break
                
                if a2_continue_clicked:
                    root.destroy()
                    break
                    
                time.sleep(1 / 240)
            
            root.run_js_code("window.removeEventListener('click', _loopClick);")
            root.run_js_code("window.removeEventListener('click', _continueClick);")
            a2_break = True
        
        Thread(target=whileCheck, daemon=True).start()
        
        def loopClick(clientX, clientY):
            nonlocal a2_loop_clicked
            if clientX <= w * const.FINISH_UI_BUTTON_SIZE and clientY <= w * const.FINISH_UI_BUTTON_SIZE / 190 * 145:
                a2_loop_clicked = True
        
        def continueClick(clientX, clientY):
            nonlocal a2_continue_clicked
            if clientX >= w - w * const.FINISH_UI_BUTTON_SIZE and clientY >= h - w * const.FINISH_UI_BUTTON_SIZE / 190 * 145:
                a2_continue_clicked = True
        
        root.jsapi.set_attr("loopClick", loopClick)
        root.jsapi.set_attr("continueClick", continueClick)
        root.run_js_code("_loopClick = (e) => {pywebview.api.call_attr('loopClick', e.clientX, e.clientY);}")
        root.run_js_code("_continueClick = (e) => {pywebview.api.call_attr('continueClick', e.clientX, e.clientY);}")
        root.run_js_code("window.addEventListener('click-np', _loopClick);")
        root.run_js_code("window.addEventListener('click-np', _continueClick);")
        
        while not a2_break:
            p = (time.time() - animation_2_start_time) / animation_2_time
            if p > 1.0: break
            phicore.settlementAnimationFrame(p)
        
        while not a2_break:
            phicore.settlementAnimationFrame(1.0)
    
    mixer.music.fadeout(250)
    Chart_Finish_Animation()

def updateCoreConfig():
    global PhiCoreConfigObject
    
    PhiCoreConfigObject = phicore.PhiCoreConfig(
        SETTER = lambda vn, vv: globals().update({vn: vv}),
        root = root, w = w, h = h,
        chart_information = chart_information,
        chart_obj = chart_obj,
        Resource = Resource,
        globalNoteWidth = globalNoteWidth,
        note_max_size_half = note_max_size_half, audio_length = audio_length,
        raw_audio_length = raw_audio_length, show_start_time = float("nan"),
        chart_image = chart_image,
        clickeffect_randomblock_roundn = clickeffect_randomblock_roundn,
        LoadSuccess = LoadSuccess, chart_res = chart_res,
        cksmanager = cksmanager,
        enable_clicksound = enable_clicksound, rtacc = rtacc,
        noautoplay = noautoplay, showfps = showfps, lfdaot = lfdaot,
        speed = speed, render_range_more = render_range_more,
        render_range_more_scale = render_range_more_scale,
        debug = debug, combotips = combotips, noplaychart = noplaychart,
        clicksound_volume = clicksound_volume,
        musicsound_volume = musicsound_volume,
        enable_controls = enable_controls
    )
    phicore.CoreConfigure(PhiCoreConfigObject)

logging.info("Loading Window...")
root = webcv.WebCanvas(
    width = 1, height = 1,
    x = -webcv.screen_width, y = -webcv.screen_height,
    title = "PhigrosPlayer - Simulator",
    debug = "--debug" in sys.argv,
    resizable = False,
    frameless = "--frameless" in sys.argv,
    renderdemand = "--renderdemand" in sys.argv,
    renderasync = "--renderasync" in sys.argv,
    jslog = "--enable-jslog" in sys.argv,
    jslog_path = sys.argv[sys.argv.index("--jslog-path")] if "--jslog-path" in sys.argv else "./ppr-jslog-nofmt.js"
)

def init():
    global webdpr
    global lowquality, lowquality_scale
    global w, h
    global Resource
    
    if webcv.disengage_webview:
        socket_webviewbridge.hook(root)

    w, h, webdpr, _, _ = root.init_window_size_and_position(0.6)
    
    webdpr = root.run_js_code("window.devicePixelRatio;")
    if webdpr != 1.0:
        lowquality = True
        lowquality_scale *= 1.0 / webdpr # ...?

    if lowquality:
        root.run_js_code(f"lowquality_scale = {lowquality_scale};")

    root.run_js_code(f"lowquality_imjscvscale_x = {lowquality_imjscvscale_x};")
    root.run_js_code(f"lowquality_imjs_maxsize = {lowquality_imjs_maxsize};")
    root.run_js_code(f"enable_jscanvas_bitmap = {enable_jscanvas_bitmap};")
    root.run_js_code(f"RPEVersion = {chart_obj.META.RPEVersion if CHART_TYPE == const.CHART_TYPE.RPE else -1};")
    
    rw, rh = w, h
    if usu169:
        ratio = w / h
        if ratio > 16 / 9:
            w = int(h * 16 / 9)
        else:
            h = int(w / 16 * 9)
        root.run_js_code("usu169 = true;")
    root.run_js_code(f"resizeCanvas({rw}, {rh}, {{willReadFrequently: {render_video}}});")
        
    Resource = loadResource()

    if wl_more_chinese:
        root.run_js_code("setWlMoreChinese();")

    updateCoreConfig()

    Thread(target=showStart, daemon=True).start()
    root.wait_for_close()
    atexit_run()

def atexit_run():
    tempdir.clearTempDir()
    needrelease.run()
    exitfunc(0)

Thread(target=root.init, args=(init, ), daemon=True).start()
root.start()
atexit_run()
