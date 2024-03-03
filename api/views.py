from rest_framework import generics, status
from .serializers import RoomSerializer, CreateRoomSerializer, UpdateRoomSerializer
from .models import Room
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http.response import JsonResponse

class RoomView(generics.ListAPIView):
    """
    API view for retrieving a list of rooms.
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class GetRoom(APIView):
    """
    API view for retrieving a room based on a given code.

    Parameters:
    - request: The HTTP request object.
    - format: The format of the response data (default: None).

    Returns:
    - If the code parameter is found in the request, returns the room data along with the 'is_host' flag.
    - If the code parameter is not found in the request, returns a 'Bad Request' response.
    - If the room with the given code is not found, returns a 'Room Not Found' response.

    """
    serializer_class = RoomSerializer
    lookup_url_kwarg = 'code'

    def get(self, request, format=None):
        code = request.GET.get(self.lookup_url_kwarg)
        if code != None:
            room = Room.objects.filter(code=code)
            if len(room) > 0:
                data = RoomSerializer(room[0]).data
                data['is_host'] = self.request.session.session_key == room[0].host
                return JsonResponse(data, status=status.HTTP_200_OK)
            return JsonResponse({'Room Not Found': 'Invalid Room Code.'}, status=status.HTTP_404_NOT_FOUND)
        
        return JsonResponse({'Bad Request': 'Code parameter not found in request.'}, status=status.HTTP_400_BAD_REQUEST)
    
class JoinRoom(APIView):
    """
    API endpoint for joining a room.

    This view allows users to join a room by providing a valid room code.
    If the room code is valid, the user's session is updated with the room code.

    Methods:
    - post: Handles the POST request for joining a room.
    """

    lookup_url_kwarg = 'code'

    def post(self, request, format=None):
        """
        Handles the POST request for joining a room.

        Args:
        - request: The HTTP request object.
        - format: The format of the response data (default: None).

        Returns:
        - A Response object with a success message if the room is joined successfully.
        - A Response object with an error message if the room code is invalid or the post data is invalid.
        """
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

        code = request.data.get(self.lookup_url_kwarg)

        if code != None:
            room_result = Room.objects.filter(code=code)
            if len(room_result) > 0:
                room = room_result[0]
                self.request.session['room_code'] = code
                return Response({'message' : 'Room Joined'}, status=status.HTTP_200_OK)
            
            return Response({'Bad Request': 'Invalid Room Code.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'Bad Request': 'Invalid post data, do not find a key.'}, status=status.HTTP_400_BAD_REQUEST)

class CreateRoomView(APIView):
    """
    API view for creating a room.

    Methods:
    - get: Not allowed. Returns a 405 Method Not Allowed response.
    - post: Creates a new room with the provided data.
            If the session does not exist, it creates a new session.
            If the room already exists, it updates the existing room.
            Returns the serialized room data with the appropriate status code.
            If the data is invalid, returns a 400 Bad Request response.
    """
    serializer_class = CreateRoomSerializer

    def get(self, request, *args, **kwargs):
        return Response({'detail': 'Method "GET" not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def post(self, request, format=None):
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            guest_can_pause = serializer.data.get('guest_can_pause')
            votes_to_skip = serializer.data.get('votes_to_skip')
            host = self.request.session.session_key
            queryset = Room.objects.filter(host=host)
            if queryset.exists():
                room = queryset[0]
                room.guest_can_pause = guest_can_pause
                room.votes_to_skip = votes_to_skip
                room.save(update_fields=['guest_can_pause', 'votes_to_skip'])
                self.request.session['room_code'] = room.code
                return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
            else:
                room = Room(host=host, guest_can_pause=guest_can_pause,
                            votes_to_skip=votes_to_skip)
                room.save()
                self.request.session['room_code'] = room.code
                return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)

        return Response({'Bad Request': 'Invalid data...'}, status=status.HTTP_400_BAD_REQUEST)
    
class UserInRoom(APIView):
    """
    API view for retrieving the room code associated with the user's session.
    """

    def get(self, request, format=None):
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

        data = {
            'code': self.request.session.get('room_code')
        }

        return JsonResponse(data, status=status.HTTP_200_OK)
    
class LeaveRoom(APIView):
    """
    API view for leaving a room.
    """

    def post(self, request, format=None):
        """
        Handles the POST request to leave a room.

        Args:
            request (HttpRequest): The HTTP request object.
            format (str, optional): The format of the response. Defaults to None.

        Returns:
            Response: The response object with a success message.
        """
        if 'room_code' in self.request.session:
            self.request.session.pop('room_code')
            host_id = self.request.session.session_key
            room_results = Room.objects.filter(host=host_id)
            if len(room_results) > 0:
                room = room_results[0]
                room.delete()
        
        return Response({'Message': 'Success'}, status=status.HTTP_200_OK)
    
class UpdateRoom(APIView):
    """
    API view for updating a room.

    Methods:
    - patch: Update the room with the provided data.
    """

    serializer_class = UpdateRoomSerializer

    def patch(self, request, format=None):
        """
        Update the room with the provided data.

        Parameters:
        - request: The HTTP request object.
        - format: The format of the response data (default: None).

        Returns:
        - Response: The HTTP response object.
        """

        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

            
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            guest_can_pause = serializer.data.get('guest_can_pause')
            votes_to_skip = serializer.data.get('votes_to_skip')
            code = serializer.data.get('code')

            queryset = Room.objects.filter(code=code)
            if not queryset.exists():
                return Response({'msg': 'Room not found.'}, status=status.HTTP_404_NOT_FOUND)

            room = queryset[0]
            user_id = self.request.session.session_key
            if room.host != user_id:
                return Response({'msg': 'You are not the host of this room.'}, status=status.HTTP_403_FORBIDDEN)
            
            room.guest_can_pause = guest_can_pause
            room.votes_to_skip =  votes_to_skip
            room.save(update_fields=['guest_can_pause', 'votes_to_skip'])
            return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
        
        return Response({'Bad Request': 'Invalid data...'}, status=status.HTTP_400_BAD_REQUEST)
    