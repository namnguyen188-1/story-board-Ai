"""Deterministic contour + object color behavior, no API and no paid image calls."""
import numpy as np,cv2
from studio_hand_color import iter_color_frames
from studio_hand_color_strokes import _outline_steps,_color_regions

def frames(image,count,hold=8):
    return list(iter_color_frames(image,count,hold))
source=np.empty((180,320,3),dtype=np.uint8)
source[:]=(42,129,209)
one=frames(source,60,8)
assert len(one)==60 and np.all(one[0]==255)
assert all(np.array_equal(f,source) for f in one[-8:])
# A circular paint frontier, unlike fully painted horizontal strips.
mid=one[35]
revealed=np.all(mid==source,axis=2)
assert revealed.mean()>.10 and revealed.mean()<.90,('coverage',revealed.mean())
assert np.max(revealed.mean(axis=1))<.95,('still revealing as full width stripes',revealed.mean(axis=1).max())
assert revealed[90,160] and not revealed[0,0]
print('NO_HORIZONTAL_STRIPE_REVEAL_PASS',round(float(revealed.mean()),3),flush=True)

image=np.full((180,320,3),(233,244,222),np.uint8)
cv2.rectangle(image,(27,24),(167,141),(55,165,216),-1)
cv2.circle(image,(232,100),42,(194,60,92),-1)
cv2.line(image,(35,130),(292,25),(38,42,42),5)
contours=_outline_steps(image)
assert len(contours)>=20,len(contours)
order,regions,*_= _color_regions(image)
assert len(regions)>1,len(regions)
two=frames(image,90,10)
assert len(two)==90 and np.array_equal(two[-1],image)
ink=two[20]
dark=((ink[:,:,0]<100)&(ink[:,:,1]<100)&(ink[:,:,2]<100))
assert int(dark.sum())>=20,('contour stroke invisible',dark.sum())
assert not np.array_equal(ink,image), 'should not show full photo during sketch stage'
# Fills are progressive, final clean source, no white-frame reappearance.
blackouts=[float(np.mean(np.all(frame>246,axis=2))) for frame in two]
after_start=next(i for i,f in enumerate(blackouts) if f<.93)
assert max(blackouts[after_start:])<.985
assert max(np.diff(blackouts))<.16,max(np.diff(blackouts))
assert np.array_equal(frames(image,90,10)[28],two[28]),'non deterministic render'
print('CONTOUR_PATH_AND_OBJECT_FILL_PASS',len(contours),len(regions),flush=True)
print('NO_WHITE_FLASH_AND_DETERMINISTIC_PASS',flush=True)
